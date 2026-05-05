#!/usr/bin/env python3
"""
GPU-Accelerated Teacher Cache Precomputation
Optimized version: teacher on GPU, batched processing, async index writes
"""

import os
import sys
import json
import pickle
import logging
import hashlib
import gc
from pathlib import Path
from datetime import datetime

import torch
import pyarrow.parquet as pq

# Content-based cache key generation
def get_cache_key(input_ids):
    """Generate MD5 hash of input_ids for content-based cache lookup."""
    if isinstance(input_ids, torch.Tensor):
        if input_ids.is_cuda:
            input_ids = input_ids.cpu()
        input_ids = input_ids.contiguous()
        return hashlib.md5(input_ids.numpy().tobytes()).hexdigest()
    elif isinstance(input_ids, (list, tuple)):
        arr = torch.tensor(input_ids, dtype=torch.long)
        return hashlib.md5(arr.numpy().tobytes()).hexdigest()
    else:
        return hashlib.md5(str(input_ids).encode()).hexdigest()

# Setup logging with immediate flush
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/mnt/bigssd/precompute_teacher_cache_gpu.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Force flush
for handler in logging.root.handlers:
    handler.flush = lambda: None


# ============================================================
# CONFIGURATION
# ============================================================

class Config:
    """Precompute configuration."""
    # Model paths
    teacher_model_path: str = "/data/models/FrankenV8-Final/"
    
    # Data paths
    curatedthoughts_dir: str = "/data/datasets/curatedthoughts/"
    openthoughts_dir: str = "/data/datasets/openthoughts2-1m/"
    
    # Cache paths (SSD — fast access)
    cache_dir: str = "/mnt/bigssd/teacher_cache/"
    
    # Teacher layers to cache
    teacher_layers = [8, 16, 24, 32, 40, 48]
    
    # Processing
    batch_size: int = 1  # Conservative to avoid OOM on 130GB GPU
    max_seq_len: int = 512
    save_every: int = 50  # Save index every N samples
    
    # Synthetic data ratio
    synthetic_ratio: float = 0.3


# ============================================================
# TEACHER MODEL (Franken V8)
# ============================================================

class TeacherModelWrapper:
    """Wrapper for Franken V8 teacher model. Loads to GPU for fast inference."""
    
    def __init__(self, model_path: str, device: str = "cuda"):
        self.device = device
        self.model = None
        self.tokenizer = None
        self._load_model(model_path)
    
    def _load_model(self, model_path: str):
        """Load teacher model to GPU."""
        logging.info(f"Loading teacher model from {model_path}")
        
        model_dir = Path(model_path)
        if model_path.endswith('.pt'):
            model_dir = Path(model_path).parent
        
        config_json = model_dir / "config.json"
        
        if not config_json.exists():
            logging.warning(f"No config.json found in {model_dir}")
            return
        
        try:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(str(model_dir), trust_remote_code=True)
            logging.info(f"Loaded config: {config.model_type}, {config.num_hidden_layers} layers")
        except Exception as e:
            logging.warning(f"Failed to load config: {e}")
            return
        
        checkpoint_path = None
        if model_path.endswith('.pt') and os.path.exists(model_path):
            checkpoint_path = model_path
        else:
            candidates = list(model_dir.glob('*.pt'))
            if candidates:
                final_model = model_dir / 'final_model.pt'
                if final_model.exists():
                    checkpoint_path = str(final_model)
                else:
                    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    checkpoint_path = str(candidates[0])
        
        if not checkpoint_path or not os.path.exists(checkpoint_path):
            logging.warning(f"No checkpoint found in {model_dir}")
            return
        
        logging.info(f"Loading checkpoint: {checkpoint_path}")
        
        try:
            from transformers import AutoModelForCausalLM
            self.model = AutoModelForCausalLM.from_config(config, trust_remote_code=True)
            self.model = self.model.to(torch.bfloat16)
            logging.info("Model architecture instantiated from config")
        except Exception as e:
            logging.warning(f"Failed to instantiate model from config: {e}")
            try:
                self.model = AutoModelForCausalLM.from_pretrained(
                    str(model_dir),
                    config=config,
                    torch_dtype=torch.bfloat16,
                    device_map="cpu",
                    trust_remote_code=True,
                    state_dict={},
                )
                logging.info("Model loaded with empty state dict")
            except Exception as e2:
                logging.warning(f"Fallback also failed: {e2}")
                return
        
        try:
            checkpoint = torch.load(checkpoint_path, map_location="cpu")
            
            state_dict = None
            if isinstance(checkpoint, dict):
                if 'model_state_dict' in checkpoint:
                    state_dict = checkpoint['model_state_dict']
                    logging.info("Found model_state_dict in checkpoint")
                elif 'state_dict' in checkpoint:
                    state_dict = checkpoint['state_dict']
                    logging.info("Found state_dict in checkpoint")
                else:
                    state_dict = checkpoint
                    logging.info("Using raw checkpoint dict as state_dict")
            
            if state_dict is not None:
                cleaned_state_dict = {}
                for k, v in state_dict.items():
                    if k.startswith('module.'):
                        cleaned_state_dict[k[7:]] = v
                    else:
                        cleaned_state_dict[k] = v
                
                missing, unexpected = self.model.load_state_dict(cleaned_state_dict, strict=False)
                if missing:
                    logging.info(f"Missing keys: {len(missing)}")
                if unexpected:
                    logging.info(f"Unexpected keys: {len(unexpected)}")
                
                logging.info(f"Checkpoint loaded: {len(cleaned_state_dict)} parameters")
            
            self.model.eval()
            self.model = self.model.to(self.device)
            
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True)
            except:
                self.tokenizer = None
                logging.info("No tokenizer found, will use student tokenizer")
            
            logging.info("Teacher model loaded successfully")
            
        except Exception as e:
            logging.error(f"Failed to load checkpoint: {e}")
            self.model = None
    
    @torch.no_grad()
    def get_hidden_states(self, input_ids: torch.Tensor, layers: list) -> dict:
        """Get hidden states from specified layers."""
        if self.model is None:
            return {}
        
        input_ids = input_ids.to(self.device)
        
        try:
            outputs = self.model(input_ids=input_ids, output_hidden_states=True)
            hidden_states = outputs.hidden_states
            
            result = {}
            for layer_idx in layers:
                if layer_idx < len(hidden_states):
                    result[layer_idx] = hidden_states[layer_idx]
            
            return result
        except Exception as e:
            logging.warning(f"Teacher forward pass failed: {e}")
            return {}


# ============================================================
# DATASET
# ============================================================

class StreamingParquetDataset:
    """Streaming dataset from Parquet files."""
    
    def __init__(self, data_dirs: list, synthetic_ratio: float = 0.3):
        self.data_dirs = data_dirs
        self.synthetic_ratio = synthetic_ratio
        self.files = self._discover_files()
    
    def _discover_files(self):
        """Discover all Parquet files recursively."""
        files = []
        for data_dir in self.data_dirs:
            if os.path.exists(data_dir):
                for root, dirs, fnames in os.walk(data_dir):
                    for f in fnames:
                        if f.endswith('.parquet'):
                            files.append(os.path.join(root, f))
        return sorted(files)
    
    def _format_conversation(self, row: dict) -> str:
        """Format a conversation row into text."""
        # Try different column names
        for key in ['text', 'conversation', 'messages', 'content', 'prompt']:
            if key in row:
                val = row[key]
                
                # Handle numpy arrays -> convert to list
                if hasattr(val, 'tolist'):
                    val = val.tolist()
                
                # Handle list of message dicts (conversation format)
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                    texts = []
                    for msg in val:
                        if isinstance(msg, dict):
                            for msg_key in ['value', 'content', 'text', 'message']:
                                if msg_key in msg and msg[msg_key]:
                                    texts.append(str(msg[msg_key]))
                                    break
                    return "\n\n".join(texts) if texts else str(val)

                
                # Handle single dict
                elif isinstance(val, dict):
                    for msg_key in ['value', 'content', 'text', 'message']:
                        if msg_key in val and val[msg_key]:
                            return str(val[msg_key])
                    return str(val)
                
                # Handle string
                elif isinstance(val, str) and val.strip():
                    return val
                
                # Fallback: convert to string
                elif val is not None:
                    s = str(val)
                    if s.strip():
                        return s
        
        # Fallback: concatenate all string columns
        parts = []
        for k, v in row.items():
            if isinstance(v, str) and v.strip():
                parts.append(v)
            elif hasattr(v, 'tolist'):
                v_list = v.tolist()
                if isinstance(v_list, list) and len(v_list) > 0 and isinstance(v_list[0], dict):
                    for msg in v_list:
                        if isinstance(msg, dict):
                            for msg_key in ['value', 'content', 'text']:
                                if msg_key in msg and msg[msg_key]:
                                    parts.append(str(msg[msg_key]))
                                    break
        return "\n\n".join(parts) if parts else ""


def _process_batch(teacher, tokenizer, texts, temp_ids, cache_dir, cache_index, config):
    """Process a batch of texts on GPU."""
    try:
        # Tokenize batch
        tokens = tokenizer(
            texts,
            truncation=True,
            max_length=config.max_seq_len,
            padding=True,
            return_tensors="pt"
        )
        input_ids = tokens['input_ids'].to('cuda')
        
        # Compute teacher hidden states on GPU
        with torch.no_grad():
            teacher_hidden = teacher.get_hidden_states(
                input_ids,
                config.teacher_layers
            )
        
        # Move to CPU for saving with content-based keys
        if teacher_hidden:
            for i, temp_id in enumerate(temp_ids):
                # Generate content-based key from tokenized input
                single_input_ids = tokens['input_ids'][i]
                # Remove padding tokens for consistent hashing
                if hasattr(tokenizer, 'pad_token_id') and tokenizer.pad_token_id is not None:
                    mask = single_input_ids != tokenizer.pad_token_id
                    single_input_ids = single_input_ids[mask]
                    # Ensure at least 1 token remains
                    if len(single_input_ids) == 0:
                        single_input_ids = tokens['input_ids'][i][:1]
                
                sample_id = get_cache_key(single_input_ids)
                
                # Skip if already cached
                if sample_id in cache_index:
                    continue
                
                single_hidden = {
                    layer: tensor[i].cpu() if tensor is not None else None
                    for layer, tensor in teacher_hidden.items()
                }
                
                cache_path = cache_dir / f"{sample_id}.pkl"
                with open(cache_path, 'wb') as f:
                    pickle.dump(single_hidden, f)
                
                cache_index[sample_id] = str(cache_path)
        
        # Clear GPU cache
        torch.cuda.empty_cache()
        
    except Exception as e:
        logging.warning(f"Batch failed: {e}")
        # Mark all as failed but continue
        for temp_id in temp_ids:
            cache_index[temp_id] = "ERROR"


def _save_index(index_path, cache_index):
    """Save index atomically."""
    temp_path = str(index_path) + ".tmp"
    with open(temp_path, 'w') as f:
        json.dump(cache_index, f)
    os.replace(temp_path, index_path)


# ============================================================
# MAIN
# ============================================================

def main():
    logging.info("=" * 70)
    logging.info("GPU-ACCELERATED TEACHER CACHE PRECOMPUTATION")
    logging.info("=" * 70)
    
    config = Config()
    
    # Setup cache directory
    cache_dir = Path(config.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Load or create cache index
    index_path = cache_dir / "index.json"
    cache_index = {}
    if index_path.exists():
        with open(index_path, 'r') as f:
            cache_index = json.load(f)
        logging.info(f"Resuming: {len(cache_index)} samples already cached")
    
    # Load teacher model to GPU
    logging.info("Loading Franken V8 teacher model to GPU...")
    teacher = TeacherModelWrapper(config.teacher_model_path, device="cuda")
    
    if teacher.model is None:
        logging.error("Failed to load teacher model")
        return False
    
    logging.info(f"Teacher loaded. GPU memory used: {torch.cuda.memory_allocated() / 1e9:.1f}GB")
    
    # Load tokenizer from Qwen3-0.6B (FrankenV8 tokenizer is broken)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        "/data/models/Qwen3-0.6B/",
        trust_remote_code=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load dataset
    dataset = StreamingParquetDataset([
        config.curatedthoughts_dir,
        config.openthoughts_dir,
    ], synthetic_ratio=config.synthetic_ratio)
    
    real_files = dataset.files
    logging.info(f"Dataset: {len(real_files)} real files, synthetic ratio {config.synthetic_ratio}")
    
    if not real_files:
        logging.error("No data files found")
        return False
    
    logging.info(f"Found {len(real_files)} real data files")
    
    # Process all files
    batch_size = config.batch_size
    cached_samples = 0
    skipped_samples = 0
    error_samples = 0
    total_samples = 0
    
    for file_idx, file_path in enumerate(real_files):
        logging.info(f"Processing file {file_idx+1}/{len(real_files)}: {file_path}")
        
        try:
            table = pq.read_table(file_path)
            df = table.to_pandas()
            
            # Process in batches for GPU efficiency
            batch_texts = []
            batch_ids = []
            
            for row_idx, row in df.iterrows():
                text = dataset._format_conversation(row.to_dict())
                if not text:
                    continue
                
                # Use temporary ID - _process_batch will generate content-based key
                temp_id = f"file{file_idx}_row{row_idx}"
                batch_texts.append(text)
                batch_ids.append(temp_id)
                
                # Process batch when full
                if len(batch_texts) >= batch_size:
                    _process_batch(
                        teacher, tokenizer, batch_texts, batch_ids,
                        cache_dir, cache_index, config
                    )
                    cached_samples += len(batch_texts)
                    total_samples += len(batch_texts)
                    batch_texts = []
                    batch_ids = []
                    
                    # Save index periodically
                    if cached_samples % config.save_every == 0:
                        _save_index(index_path, cache_index)
                        logging.info(f"  Progress: {cached_samples} processed, {len(cache_index)} cached, {skipped_samples} skipped, {error_samples} errors")
            
            # Process remaining batch
            if batch_texts:
                _process_batch(
                    teacher, tokenizer, batch_texts, batch_ids,
                    cache_dir, cache_index, config
                )
                cached_samples += len(batch_texts)
                total_samples += len(batch_texts)
        
        except Exception as e:
            logging.warning(f"File failed: {e}")
            error_samples += 1
            continue
    
    # Final save
    _save_index(index_path, cache_index)
    
    logging.info("=" * 70)
    logging.info("PRECOMPUTATION COMPLETE")
    logging.info(f"Total processed: {total_samples}")
    logging.info(f"Cached: {cached_samples}")
    logging.info(f"Skipped: {skipped_samples}")
    logging.info(f"Errors: {error_samples}")
    logging.info(f"Unique cached: {len(cache_index)}")
    logging.info(f"Cache directory: {cache_dir}")
    logging.info("=" * 70)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
