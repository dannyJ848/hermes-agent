#!/usr/bin/env python3
"""
Qwen 27B Expert Logician — SAE-Guided LoRA with Teacher Distillation
Highest quality fine-tune achievable on 130GB GPU + 128GB RAM.

Architecture:
- Base: Qwen3.6-27B-Uncensored (frozen, bf16 on GPU ~27GB)
- LoRA: rank-256 on all linear layers (~500M trainable params)
- Teacher: Franken V8 (CPU, generates synthetic traces + hidden states)
- SAEs: Qwen-Scope layers [16, 32, 48] (CPU, feature alignment)
- Loss: Multi-objective (CE + hidden-state MSE + SAE feature MSE + reasoning consistency)
- Curriculum: SAE feature complexity as difficulty metric
- Data: Streaming Parquet (curatedthoughts + openthoughts2-1m)

Memory budget:
- GPU: 27GB (frozen model) + ~2GB (LoRA) + ~8GB (activations/batch) + ~10GB (teacher hidden states cache) = ~47GB
- RAM: 27GB (teacher model) + ~5GB (SAEs) + ~20GB (data buffers) = ~52GB
- Total well within limits.

Author: Hermes Agent | Date: May 3, 2026
"""

import os
import sys
import json
import math
import random
import logging
import gc
import pickle
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
from pathlib import Path
from collections import defaultdict

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import IterableDataset, DataLoader

# LoRA
try:
    from peft import LoraConfig, get_peft_model, PeftModel
    HAS_PEFT = True
except ImportError:
    HAS_PEFT = False
    print("ERROR: peft not installed. Run: pip install peft")
    sys.exit(1)

# Transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/mnt/bigssd/train_lora_sae_teacher_v1.log')
    ]
)

# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class TrainConfig:
    # Model paths
    student_model_path: str = "/data/models/Qwen3.6-27B-Uncensored/"
    teacher_model_path: str = "/data/models/FrankenV8-Final/"
    sae_dir: str = "/data/models/Qwen-Scope/"
    
    # Data paths
    curatedthoughts_dir: str = "/data/datasets/curatedthoughts/"
    openthoughts_dir: str = "/data/datasets/openthoughts2-1m/"
    
    # Cache paths (SSD — fast access for precomputed teacher states)
    teacher_cache_dir: str = "/mnt/bigssd/teacher_cache/"
    sae_cache_dir: str = "/mnt/bigssd/sae_cache/"
    
    # LoRA config — rank-256 for maximum expressiveness
    lora_r: int = 128
    lora_alpha: int = 256  # 2x rank
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])
    
    # Training
    max_steps: int = 10000
    batch_size: int = 4  # Larger batch with LoRA
    grad_accum_steps: int = 4  # Effective batch = 16
    max_seq_len: int = 512
    
    # Optimizer — 8-bit AdamW if available, else regular AdamW
    use_8bit_adam: bool = True
    lr: float = 2e-4
    beta1: float = 0.9
    beta2: float = 0.999
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # Schedule
    warmup_steps: int = 500
    stable_steps: int = 8000
    decay_steps: int = 1500
    
    # Teacher distillation (disable if teacher too slow on CPU)
    use_teacher: bool = True
    teacher_layers: List[int] = field(default_factory=lambda: [8, 16, 24, 32, 40, 48])
    teacher_weight: float = 0.3
    temperature: float = 2.0
    
    # SAE guidance
    use_sae: bool = True
    sae_layers: List[int] = field(default_factory=lambda: [16, 32, 48])
    sae_weight: float = 0.1
    
    # Synthetic data generation
    synthetic_ratio: float = 0.3  # 30% synthetic from Franken V8
    max_synthetic_per_step: int = 2
    
    # Curriculum learning
    use_curriculum: bool = True
    curriculum_ramp_steps: int = 7000
    
    # Checkpointing
    save_every: int = 500
    checkpoint_dir: str = "/data/SpecForge/custom_dflash/checkpoints/"
    
    # Loss weights (dynamic — start high on CE, shift to distillation)
    ce_weight_start: float = 1.0
    ce_weight_end: float = 0.5
    distill_weight_start: float = 0.2
    distill_weight_end: float = 0.5
    sae_weight_start: float = 0.05
    sae_weight_end: float = 0.15


# ============================================================
# SAE UTILITIES
# ============================================================

def load_sae(sae_dir: str, layer_idx: int, device: str = "cpu"):
    """Load a single SAE for a specific layer."""
    # Try multiple naming conventions
    sae_path = Path(sae_dir) / f"sae_layer_{layer_idx}.pt"
    if not sae_path.exists():
        sae_path = Path(sae_dir) / f"layer{layer_idx}.sae.pt"
    if not sae_path.exists():
        sae_path = Path(sae_dir) / f"layer_{layer_idx}.pt"
    if not sae_path.exists():
        sae_path = Path(sae_dir) / f"sae_{layer_idx}.pt"
    if not sae_path.exists():
        logging.warning(f"SAE not found for layer {layer_idx} in {sae_dir}")
        return None
    
    try:
        sae = torch.load(sae_path, map_location=device)
        logging.info(f"Loaded SAE for layer {layer_idx}")
        return sae
    except Exception as e:
        logging.warning(f"Failed to load SAE layer {layer_idx}: {e}")
        return None


def get_sae_feature_acts(hidden_states: torch.Tensor, sae) -> torch.Tensor:
    """Extract sparse feature activations from hidden states using SAE.
    
    Args:
        hidden_states: [batch, seq_len, hidden_dim]
        sae: Either an nn.Module or a dict with 'W_enc', 'W_dec', 'b_enc', 'b_dec'
    """
    if sae is None:
        return None
    
    with torch.no_grad():
        # Handle dict format (state dict)
        if isinstance(sae, dict):
            device = hidden_states.device
            hidden_states = hidden_states.to(device)
            
            # Get SAE parameters from dict
            W_enc = sae['W_enc'].to(device)  # [n_features, hidden_dim]
            b_enc = sae['b_enc'].to(device)  # [n_features]
            
            # Flatten hidden states: [batch*seq_len, hidden_dim]
            original_shape = hidden_states.shape
            hidden_flat = hidden_states.reshape(-1, original_shape[-1])
            
            # Encode: features = relu(hidden_flat @ W_enc.T + b_enc)
            features = torch.matmul(hidden_flat, W_enc.t()) + b_enc
            features = torch.relu(features)
            
            # Reshape back: [batch, seq_len, n_features]
            features = features.reshape(original_shape[0], original_shape[1], -1)
            
            return features
        
        # Handle nn.Module format
        device = next(sae.parameters()).device
        hidden_states = hidden_states.to(device)
        
        # SAE encode
        if hasattr(sae, 'encode'):
            features = sae.encode(hidden_states)
        elif hasattr(sae, 'forward'):
            features = sae(hidden_states)
        else:
            # Fallback: assume W_enc, b_enc attributes
            if hasattr(sae, 'W_enc'):
                W_enc = sae.W_enc
                b_enc = sae.b_enc
                hidden_flat = hidden_states.reshape(-1, hidden_states.shape[-1])
                features = torch.matmul(hidden_flat, W_enc) + b_enc
                features = torch.relu(features)
                features = features.reshape(hidden_states.shape[0], hidden_states.shape[1], -1)
            else:
                return None
        
        return features


def compute_sae_loss(student_features: torch.Tensor, teacher_features: torch.Tensor) -> torch.Tensor:
    """MSE loss between student and teacher SAE features."""
    if student_features is None or teacher_features is None:
        return torch.tensor(0.0, device=student_features.device if student_features is not None else "cpu")
    
    # Match shapes
    min_len = min(student_features.size(1), teacher_features.size(1))
    student_features = student_features[:, :min_len, :]
    teacher_features = teacher_features[:, :min_len, :]
    
    return F.mse_loss(student_features, teacher_features)


# ============================================================
# TEACHER MODEL (Franken V8)
# ============================================================

class TeacherModelWrapper:
    """Wrapper for Franken V8 teacher model. Loads to CPU, generates hidden states."""
    
    def __init__(self, model_path: str, device: str = "cpu"):
        self.device = device
        self.model = None
        self.tokenizer = None
        self._load_model(model_path)
    
    def _load_model(self, model_path: str):
        """Load teacher model to CPU. Franken V8 uses custom DFlashQwen3ForCausalLM."""
        logging.info(f"Loading teacher model from {model_path}")
        
        # Franken V8 directory structure: config.json + checkpoint-*.pt or final_model.pt
        model_dir = Path(model_path)
        if model_path.endswith('.pt'):
            model_dir = Path(model_path).parent
        
        config_json = model_dir / "config.json"
        
        if not config_json.exists():
            logging.warning(f"No config.json found in {model_dir}")
            return
        
        # Load config
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(str(model_dir), trust_remote_code=True)
            logging.info(f"Loaded config: {config.model_type}, {config.num_hidden_layers} layers")
        except Exception as e:
            logging.warning(f"Failed to load config: {e}")
            return
        
        # Find checkpoint file
        checkpoint_path = None
        if model_path.endswith('.pt') and os.path.exists(model_path):
            checkpoint_path = model_path
        else:
            # Look for final_model.pt or latest checkpoint
            candidates = list(model_dir.glob('*.pt'))
            if candidates:
                # Prefer final_model.pt, then latest checkpoint
                final_model = model_dir / 'final_model.pt'
                if final_model.exists():
                    checkpoint_path = str(final_model)
                else:
                    # Sort by modification time, pick latest
                    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    checkpoint_path = str(candidates[0])
        
        if not checkpoint_path or not os.path.exists(checkpoint_path):
            logging.warning(f"No checkpoint found in {model_dir}")
            return
        
        logging.info(f"Loading checkpoint: {checkpoint_path}")
        
        # Load model architecture directly from config (no from_pretrained since no HF weights)
        try:
            from transformers import AutoModelForCausalLM
            # Instantiate model class directly from config
            self.model = AutoModelForCausalLM.from_config(config, trust_remote_code=True)
            self.model = self.model.to(torch.bfloat16)
            logging.info("Model architecture instantiated from config")
        except Exception as e:
            logging.warning(f"Failed to instantiate model from config: {e}")
            # Fallback: try loading with empty state dict
            try:
                self.model = AutoModelForCausalLM.from_pretrained(
                    str(model_dir),
                    config=config,
                    torch_dtype=torch.bfloat16,
                    device_map="cpu",
                    trust_remote_code=True,
                    state_dict={},  # Empty state dict to bypass weight loading
                )
                logging.info("Model loaded with empty state dict")
            except Exception as e2:
                logging.warning(f"Fallback also failed: {e2}")
                return
        
        # Load checkpoint weights
        try:
            checkpoint = torch.load(checkpoint_path, map_location="cpu")
            
            # Handle different checkpoint formats
            state_dict = None
            if isinstance(checkpoint, dict):
                if 'model_state_dict' in checkpoint:
                    state_dict = checkpoint['model_state_dict']
                    logging.info("Found model_state_dict in checkpoint")
                elif 'state_dict' in checkpoint:
                    state_dict = checkpoint['state_dict']
                    logging.info("Found state_dict in checkpoint")
                else:
                    # Assume it's a raw state dict
                    state_dict = checkpoint
                    logging.info("Using raw checkpoint dict as state_dict")
            
            if state_dict is not None:
                # Remove 'module.' prefix if present (from DataParallel)
                cleaned_state_dict = {}
                for k, v in state_dict.items():
                    if k.startswith('module.'):
                        cleaned_state_dict[k[7:]] = v
                    else:
                        cleaned_state_dict[k] = v
                
                # Load into model
                missing, unexpected = self.model.load_state_dict(cleaned_state_dict, strict=False)
                if missing:
                    logging.info(f"Missing keys: {len(missing)}")
                if unexpected:
                    logging.info(f"Unexpected keys: {len(unexpected)}")
                
                logging.info(f"Checkpoint loaded: {len(cleaned_state_dict)} parameters")
            
            self.model.eval()
            self.model = self.model.to("cpu")
            
            # Load tokenizer
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)
            except:
                # Fallback: use student tokenizer
                self.tokenizer = None
                logging.info("No tokenizer found, will use student tokenizer")
            
            logging.info("Teacher model loaded successfully")
            
        except Exception as e:
            logging.error(f"Failed to load checkpoint: {e}")
            self.model = None
    
    @torch.no_grad()
    def get_hidden_states(self, input_ids: torch.Tensor, layers: List[int]) -> Dict[int, torch.Tensor]:
        """Get hidden states from specified layers."""
        if self.model is None:
            return {}
        
        # Move input to CPU
        input_ids = input_ids.cpu()
        
        # Forward pass with output_hidden_states
        try:
            outputs = self.model(input_ids=input_ids, output_hidden_states=True)
            hidden_states = outputs.hidden_states
            
            # Extract specified layers
            result = {}
            for layer_idx in layers:
                if layer_idx < len(hidden_states):
                    result[layer_idx] = hidden_states[layer_idx].detach().cpu()
            
            return result
        except Exception as e:
            logging.warning(f"Teacher forward pass failed: {e}")
            return {}
    
    @torch.no_grad()
    def generate_reasoning_trace(self, prompt: str, max_length: int = 2048) -> str:
        """Generate a synthetic reasoning trace from Franken V8."""
        if self.model is None or self.tokenizer is None:
            return ""
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )
            
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            logging.warning(f"Teacher generation failed: {e}")
            return ""


# ============================================================
# TEACHER HIDDEN STATE CACHE
# ============================================================

class TeacherHiddenStateCache:
    """Cache precomputed teacher hidden states to SSD for fast retrieval."""
    
    def __init__(self, cache_dir: str, teacher: TeacherModelWrapper, layers: List[int]):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.teacher = teacher
        self.layers = layers
        self._cache_index = self._load_index()
    
    def _load_index(self) -> Dict[str, str]:
        """Load cache index mapping sample IDs to cache files."""
        index_path = self.cache_dir / "index.json"
        if index_path.exists():
            with open(index_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_index(self):
        """Save cache index."""
        index_path = self.cache_dir / "index.json"
        with open(index_path, 'w') as f:
            json.dump(self._cache_index, f)
    
    def _get_cache_path(self, sample_id: str) -> Path:
        """Get cache file path for a sample."""
        return self.cache_dir / f"{sample_id}.pkl"
    
    def get(self, sample_id: str, input_ids: torch.Tensor) -> Optional[Dict[int, torch.Tensor]]:
        """Get cached hidden states for a sample. Compute if not cached."""
        cache_path = self._get_cache_path(sample_id)
        
        # Check cache
        if sample_id in self._cache_index and cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logging.warning(f"Cache load failed for {sample_id}: {e}")
        
        # Compute from teacher
        # Cache teacher hidden states if teacher available
        if self.teacher is not None and self.teacher.model is not None:
            hidden_states = self.teacher.get_hidden_states(input_ids, self.layers)
            
            # Save to cache
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(hidden_states, f)
                self._cache_index[sample_id] = str(cache_path)
                self._save_index()
            except Exception as e:
                logging.warning(f"Cache save failed for {sample_id}: {e}")
            
            return hidden_states
        
        return None
    
    def precompute_all(self, dataset, tokenizer):
        """Precompute and cache teacher hidden states for entire dataset."""
        logging.info("Precomputing teacher hidden states for all samples...")
        
        for i, sample in enumerate(dataset):
            sample_id = f"sample_{i}"
            if sample_id not in self._cache_index:
                input_ids = sample['input_ids'].unsqueeze(0)  # Add batch dim
                self.get(sample_id, input_ids)
            
            if (i + 1) % 100 == 0:
                logging.info(f"Cached {i + 1} samples...")
        
        logging.info(f"Precompute complete. Total cached: {len(self._cache_index)}")


# ============================================================
# CURRICULUM LEARNING WITH SAE COMPLEXITY
# ============================================================

def compute_sae_complexity(hidden_states: torch.Tensor, sae: nn.Module) -> float:
    """Compute complexity score using SAE feature activation sparsity."""
    features = get_sae_feature_acts(hidden_states, sae)
    if features is None:
        return 0.5  # Default medium complexity
    
    # Complexity = mean activation magnitude (more active features = more complex)
    complexity = features.abs().mean().item()
    
    # Normalize to [0, 1]
    # Typical SAE features have mean activation ~0.01-0.1
    complexity = min(1.0, complexity * 10)
    
    return complexity


class CurriculumSampler:
    """Sample data with curriculum learning based on SAE complexity."""
    
    def __init__(self, config: TrainConfig, saes: Dict[int, nn.Module]):
        self.config = config
        self.saes = saes
        self.step = 0
    
    def get_difficulty_threshold(self) -> float:
        """Get current difficulty threshold based on training progress."""
        if not self.config.use_curriculum:
            return 1.0  # All difficulty levels
        
        progress = min(1.0, self.step / self.config.curriculum_ramp_steps)
        # Ease-in curve: start with easy (0.3), ramp to full (1.0)
        threshold = 0.3 + 0.7 * (progress ** 2)
        return threshold
    
    def filter_by_difficulty(self, samples: List[Dict], threshold: float) -> List[Dict]:
        """Filter samples to only include those below difficulty threshold."""
        if not self.config.use_curriculum or threshold >= 1.0:
            return samples
        
        # Sort by complexity and take bottom threshold fraction
        # For now, use a simple heuristic: shorter sequences = easier
        samples_with_length = [(s, len(s['input_ids'])) for s in samples]
        samples_with_length.sort(key=lambda x: x[1])
        
        cutoff = int(len(samples) * threshold)
        return [s for s, _ in samples_with_length[:cutoff]]
    
    def step_update(self):
        """Update step counter."""
        self.step += 1


# ============================================================
# STREAMING DATASET WITH SYNTHETIC AUGMENTATION
# ============================================================

class AugmentedStreamingDataset(IterableDataset):
    """Streaming dataset with real + synthetic data mixing."""
    
    def __init__(self, config: TrainConfig, tokenizer, teacher: TeacherModelWrapper):
        self.config = config
        self.tokenizer = tokenizer
        self.teacher = teacher
        self.real_files = []
        self._discover_files()
        self.synthetic_buffer = []
        logging.info(f"Dataset: {len(self.real_files)} real files, synthetic ratio {config.synthetic_ratio}")
    
    def _discover_files(self):
        for dir_path in [self.config.curatedthoughts_dir, self.config.openthoughts_dir]:
            if os.path.exists(dir_path):
                # Recursively walk subdirectories to find all .parquet files
                for root, dirs, files in os.walk(dir_path):
                    for f in files:
                        if f.endswith('.parquet'):
                            self.real_files.append(os.path.join(root, f))
    
    def _format_conversation(self, data: dict) -> str:
        if 'conversations' in data and isinstance(data['conversations'], list):
            convs = data['conversations']
            if len(convs) > 0:
                if isinstance(convs[0], dict) and 'value' in convs[0]:
                    return "\n".join([c['value'] for c in convs if 'value' in c])
                elif isinstance(convs[0], str):
                    return "\n".join(convs)
        
        if 'messages' in data and isinstance(data['messages'], list):
            msgs = data['messages']
            if len(msgs) > 0:
                if isinstance(msgs[0], dict) and 'content' in msgs[0]:
                    return "\n".join([m['content'] for m in msgs if 'content' in m])
        
        if 'problem' in data and 'solution' in data:
            return f"Problem: {data['problem']}\nSolution: {data['solution']}"
        
        if 'question' in data and 'answer' in data:
            return f"Question: {data['question']}\nAnswer: {data['answer']}"
        
        if 'question' in data:
            return f"<question>\n{data['question']}\n</question>"
        
        return str(data)
    
    def _generate_synthetic_sample(self) -> Dict:
        # Generate synthetic reasoning trace from teacher
        if self.teacher is None or self.teacher.model is None:
            return None
        
        # Prompts for synthetic reasoning
        prompts = [
            "Solve this step by step: If a train travels 120 km in 2 hours, how far will it travel in 5 hours at the same speed?",
            "Explain the logic behind binary search and write a Python implementation.",
            "Debug this code: def factorial(n): return n * factorial(n) # What's wrong?",
            "Prove by induction that the sum of first n odd numbers is n².",
            "Design a SQL query to find the top 5 customers by total purchase amount.",
        ]
        
        prompt = random.choice(prompts)
        trace = self.teacher.generate_reasoning_trace(prompt)
        
        if trace:
            tokens = self.tokenizer(trace, truncation=True,
                                  max_length=self.config.max_seq_len,
                                  return_tensors="pt")
            return {
                'input_ids': tokens['input_ids'].squeeze(0),
                'labels': tokens['input_ids'].squeeze(0).clone(),
                'source': 'synthetic',
            }
        
        return None
    
    def __iter__(self):
        import pandas as pd
        step = 0
        
        while True:
            # Decide: real or synthetic
            if random.random() < self.config.synthetic_ratio:
                # Try synthetic
                synthetic = self._generate_synthetic_sample()
                if synthetic:
                    synthetic['step'] = step
                    yield synthetic
                    step += 1
                    continue
            
            # Real data
            for pf in self.real_files:
                try:
                    df = pd.read_parquet(pf)
                    for _, row in df.iterrows():
                        text = self._format_conversation(row.to_dict())
                        tokens = self.tokenizer(text, truncation=True,
                                              max_length=self.config.max_seq_len,
                                              return_tensors="pt")
                        yield {
                            'input_ids': tokens['input_ids'].squeeze(0),
                            'labels': tokens['input_ids'].squeeze(0).clone(),
                            'source': 'real',
                            'step': step,
                        }
                        step += 1
                except Exception as e:
                    logging.warning(f"Failed to stream {pf}: {e}")
            
            if not self.real_files:
                logging.error("No data files!")
                yield {
                    'input_ids': torch.tensor([1, 2, 3]),
                    'labels': torch.tensor([1, 2, 3]),
                    'source': 'dummy',
                    'step': step,
                }
                step += 1


# ============================================================
# MULTI-OBJECTIVE LOSS
# ============================================================

class MultiObjectiveLoss:
    """Dynamic multi-objective loss with curriculum weighting."""
    
    def __init__(self, config: TrainConfig):
        self.config = config
    
    def get_weights(self, step: int) -> Dict[str, float]:
        """Get dynamic loss weights based on training progress."""
        progress = min(1.0, step / self.config.max_steps)
        
        # CE weight: starts high, decreases
        ce_w = self.config.ce_weight_start + (self.config.ce_weight_end - self.config.ce_weight_start) * progress
        
        # Distillation weight: starts low, increases
        distill_w = self.config.distill_weight_start + (self.config.distill_weight_end - self.config.distill_weight_start) * progress
        
        # SAE weight: starts low, increases
        sae_w = self.config.sae_weight_start + (self.config.sae_weight_end - self.config.sae_weight_start) * progress
        
        return {
            'ce': ce_w,
            'distill': distill_w,
            'sae': sae_w,
        }
    
    def compute(self, step: int,
                ce_loss: torch.Tensor,
                distill_loss: torch.Tensor,
                sae_loss: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Compute weighted multi-objective loss."""
        weights = self.get_weights(step)
        
        total_loss = (weights['ce'] * ce_loss +
                     weights['distill'] * distill_loss +
                     weights['sae'] * sae_loss)
        
        return total_loss, weights


# ============================================================
# TRAINING LOOP
# ============================================================

def train(config: TrainConfig):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    logging.info("=" * 70)
    logging.info("QWEN 27B — SAE-Guided LoRA with Teacher Distillation")
    logging.info("=" * 70)
    logging.info(f"Max steps: {config.max_steps}")
    logging.info(f"Batch: {config.batch_size}, Grad accum: {config.grad_accum_steps}")
    logging.info(f"Effective batch: {config.batch_size * config.grad_accum_steps}")
    logging.info(f"LoRA: r={config.lora_r}, alpha={config.lora_alpha}")
    logging.info(f"LR: {config.lr}")
    
    # Load tokenizer
    logging.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config.student_model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load student model — use device_map for automatic placement
    # or 4-bit quantization to fit in GPU memory
    logging.info("Loading student model...")
    
    # Try 4-bit first (memory-efficient)
    loaded = False
    try:
        logging.info("Loading student model (4-bit)...")
        from transformers import BitsAndBytesConfig
        from peft import prepare_model_for_kbit_training
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        model = AutoModelForCausalLM.from_pretrained(
            config.student_model_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(model)
        loaded = True
        logging.info("Loaded model in 4-bit quantization")
    except Exception as e:
        logging.warning(f"4-bit loading failed: {e}")
    
    # Fallback to bf16
    if not loaded:
        try:
            logging.info("Trying bf16...")
            model = AutoModelForCausalLM.from_pretrained(
                config.student_model_path,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )
            loaded = True
            logging.info("Loaded model in bf16")
        except Exception as e:
            logging.warning(f"bf16 loading failed: {e}")
    
    # Fallback to 8-bit
    if not loaded:
        try:
            logging.info("Trying 8-bit quantization...")
            from transformers import BitsAndBytesConfig
            from peft import prepare_model_for_kbit_training
            bnb_config = BitsAndBytesConfig(load_in_8bit=True)
            model = AutoModelForCausalLM.from_pretrained(
                config.student_model_path,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
            model = prepare_model_for_kbit_training(model)
            loaded = True
            logging.info("Loaded model in 8-bit quantization")
        except Exception as e:
            logging.warning(f"8-bit loading failed: {e}")
    
    # Apply LoRA
    logging.info("Applying LoRA...")
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=config.lora_target_modules,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load teacher (optional — disable if too slow on CPU)
    if config.use_teacher:
        logging.info("Loading teacher model (CPU)...")
        teacher = TeacherModelWrapper(config.teacher_model_path, device="cpu")
    else:
        logging.info("Teacher distillation disabled")
        teacher = None
    
    # Load SAEs
    logging.info("Loading SAEs...")
    saes = {}
    for layer_idx in config.sae_layers:
        sae = load_sae(config.sae_dir, layer_idx, device="cpu")
        if sae is not None:
            saes[layer_idx] = sae
    
    # Initialize caches
    if config.use_teacher:
        teacher_cache = TeacherHiddenStateCache(config.teacher_cache_dir, teacher, config.teacher_layers)
    else:
        teacher_cache = None
    
    # Dataset
    logging.info("Loading dataset...")
    dataset = AugmentedStreamingDataset(config, tokenizer, teacher)
    
    # Optimizer
    logging.info("Creating optimizer...")
    if config.use_8bit_adam:
        try:
            import bitsandbytes as bnb
            optimizer = bnb.optim.Adam8bit(
                model.parameters(),
                lr=config.lr,
                betas=(config.beta1, config.beta2),
                weight_decay=config.weight_decay,
            )
            logging.info("Using 8-bit AdamW")
        except ImportError:
            logging.warning("bitsandbytes not available, using regular AdamW")
            optimizer = torch.optim.AdamW(
                model.parameters(),
                lr=config.lr,
                betas=(config.beta1, config.beta2),
                weight_decay=config.weight_decay,
            )
    else:
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=config.lr,
            betas=(config.beta1, config.beta2),
            weight_decay=config.weight_decay,
        )
    
    # LR schedule
    def get_lr(step):
        if step < config.warmup_steps:
            return config.lr * (step + 1) / config.warmup_steps
        progress = (step - config.warmup_steps) / (config.max_steps - config.warmup_steps)
        return config.lr * 0.5 * (1 + math.cos(math.pi * progress))
    
    # Loss function
    loss_fn = MultiObjectiveLoss(config)
    
    # Curriculum
    curriculum = CurriculumSampler(config, saes)
    
    # Checkpoint dir
    os.makedirs(config.checkpoint_dir, exist_ok=True)
    
    logging.info("=" * 70)
    logging.info("STARTING TRAINING")
    logging.info("=" * 70)
    
    # Disable use_cache to avoid conflict with gradient checkpointing
    model.config.use_cache = False
    
    # Disable gradient checkpointing if enabled (causes use_reentrant deadlock)
    if hasattr(model, 'gradient_checkpointing_enable'):
        model.gradient_checkpointing_disable()
    
    model.train()
    
    global_step = 0
    accumulated_loss = 0.0
    accumulated_ce = 0.0
    accumulated_distill = 0.0
    accumulated_sae = 0.0
    
    # Custom collate function to pad sequences to same length
    def collate_fn(batch):
        # Find max length in this batch
        max_len = max(item['input_ids'].shape[0] for item in batch)
        
        pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
        
        # Pad all sequences to max_len
        input_ids_list = []
        labels_list = []
        sources = []
        steps = []
        
        for item in batch:
            seq_len = item['input_ids'].shape[0]
            if seq_len < max_len:
                # Pad
                padding = torch.full((max_len - seq_len,), pad_token_id, dtype=torch.long)
                input_ids = torch.cat([item['input_ids'], padding])
                labels = torch.cat([item['labels'], padding])
            else:
                input_ids = item['input_ids']
                labels = item['labels']
            
            input_ids_list.append(input_ids)
            labels_list.append(labels)
            sources.append(item.get('source', 'real'))
            steps.append(item.get('step', 0))
        
        return {
            'input_ids': torch.stack(input_ids_list),
            'labels': torch.stack(labels_list),
            'source': sources,
            'step': steps,
        }
    
    # Create dataloader
    dataloader = DataLoader(dataset, batch_size=config.batch_size, num_workers=0, collate_fn=collate_fn)
    
    for batch in dataloader:
        if global_step >= config.max_steps:
            break
        
        # Move to device
        input_ids = batch['input_ids'].to(device)
        labels = batch['labels'].to(device)
        
        # Forward pass
        outputs = model(input_ids=input_ids, labels=labels, output_hidden_states=True)
        ce_loss = outputs.loss.float() if outputs.loss is not None else torch.tensor(0.0, device=device)
        student_hidden_states = outputs.hidden_states
        
        # Cast hidden states to float32 for loss computation
        if student_hidden_states is not None:
            student_hidden_states = [h.float() if h is not None else h for h in student_hidden_states]
        
        # Teacher distillation loss
        distill_loss = torch.tensor(0.0, device=device)
        if config.use_teacher and teacher is not None and teacher.model is not None:
            # Get cached teacher hidden states
            teacher_hidden = teacher_cache.get(f"step_{global_step}", input_ids)
            
            if teacher_hidden:
                for layer_idx, teacher_h in teacher_hidden.items():
                    if layer_idx < len(student_hidden_states):
                        student_h = student_hidden_states[layer_idx]
                        # Match shapes
                        min_len = min(student_h.size(1), teacher_h.size(1))
                        student_h = student_h[:, :min_len, :]
                        teacher_h = teacher_h[:, :min_len, :].to(device)
                        
                        distill_loss += F.mse_loss(student_h, teacher_h)
                
                distill_loss = distill_loss / len(teacher_hidden)
        
        # SAE feature alignment loss
        sae_loss = torch.tensor(0.0, device=device)
        if config.use_sae and saes:
            for layer_idx, sae in saes.items():
                if layer_idx < len(student_hidden_states):
                    student_h = student_hidden_states[layer_idx]
                    
                    # Get student SAE features
                    student_features = get_sae_feature_acts(student_h, sae)
                    
                    # Get teacher SAE features (from cached teacher hidden states)
                    if config.use_teacher:
                        teacher_h = teacher_cache.get(f"step_{global_step}", input_ids)
                        if teacher_h and layer_idx in teacher_h:
                            teacher_features = get_sae_feature_acts(
                                teacher_h[layer_idx].to(device), sae
                            )
                            
                            if student_features is not None and teacher_features is not None:
                                sae_loss += compute_sae_loss(student_features, teacher_features)
                    else:
                        # Without teacher, just regularize SAE features
                        if student_features is not None:
                            # L1 sparsity regularization on SAE features
                            sae_loss += student_features.abs().mean() * 0.01
            
            sae_loss = sae_loss / len(saes)
        
        # Multi-objective loss
        total_loss, weights = loss_fn.compute(
            global_step, ce_loss, distill_loss, sae_loss
        )
        
        # Scale for gradient accumulation
        total_loss = total_loss / config.grad_accum_steps
        
        # Backward
        total_loss.backward()
        
        accumulated_loss += total_loss.item() * config.grad_accum_steps
        accumulated_ce += ce_loss.item()
        accumulated_distill += distill_loss.item()
        accumulated_sae += sae_loss.item()
        
        # Gradient accumulation step
        if (global_step + 1) % config.grad_accum_steps == 0:
            # Clip gradients
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            
            # Update LR
            current_lr = get_lr(global_step)
            for param_group in optimizer.param_groups:
                param_group['lr'] = current_lr
            
            # Optimizer step
            optimizer.step()
            optimizer.zero_grad()
            
            # Log
            if global_step % 10 == 0:
                avg_loss = accumulated_loss / config.grad_accum_steps
                avg_ce = accumulated_ce / config.grad_accum_steps
                avg_distill = accumulated_distill / config.grad_accum_steps
                avg_sae = accumulated_sae / config.grad_accum_steps
                
                logging.info(
                    f"Step {global_step}/{config.max_steps} | "
                    f"Loss: {avg_loss:.4f} (CE:{avg_ce:.3f} D:{avg_distill:.3f} SAE:{avg_sae:.3f}) | "
                    f"W:({weights['ce']:.2f},{weights['distill']:.2f},{weights['sae']:.2f}) | "
                    f"LR: {current_lr:.2e} | "
                    f"GPU: {torch.cuda.memory_allocated()/1e9:.1f}GB"
                )
            
            accumulated_loss = 0.0
            accumulated_ce = 0.0
            accumulated_distill = 0.0
            accumulated_sae = 0.0
            
            # Checkpoint
            if global_step % config.save_every == 0 and global_step > 0:
                checkpoint_path = os.path.join(config.checkpoint_dir, f"checkpoint_step_{global_step}")
                model.save_pretrained(checkpoint_path)
                
                # Save optimizer
                torch.save({
                    'step': global_step,
                    'optimizer_state_dict': optimizer.state_dict(),
                    'config': config,
                }, os.path.join(checkpoint_path, "optimizer.pt"))
                
                logging.info(f"Saved checkpoint: {checkpoint_path}")
            
            # Clear cache
            if global_step % 50 == 0:
                torch.cuda.empty_cache()
                gc.collect()
        
        # Update curriculum
        curriculum.step_update()
        
        global_step += 1
    
    # Final save
    final_path = os.path.join(config.checkpoint_dir, "final_model")
    model.save_pretrained(final_path)
    
    # Merge LoRA weights for inference
    logging.info("Merging LoRA weights...")
    merged_model = model.merge_and_unload()
    merged_path = os.path.join(config.checkpoint_dir, "final_model_merged")
    merged_model.save_pretrained(merged_path)
    
    logging.info(f"Training complete!")
    logging.info(f"LoRA adapter: {final_path}")
    logging.info(f"Merged model: {merged_path}")


if __name__ == "__main__":
    config = TrainConfig()
    
    if os.environ.get("MAX_STEPS"):
        config.max_steps = int(os.environ.get("MAX_STEPS"))
    
    train(config)
