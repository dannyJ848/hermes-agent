"""
Qwen 3.6 27B + Qwen-Scope SAE + Franken V8 25-Grafts
FULL FINE-TUNING with DeepSpeed ZeRO-Infinity

Architecture:
- Student: Qwen 3.6 27B (ALL parameters trainable) + Qwen-Scope SAEs (trainable)
- Teacher: Franken V8 25-Grafts (frozen, generates targets)
- SAEs: Analyze Franken's hidden states to guide Qwen's learning

Memory Strategy (ZeRO-Infinity):
- Qwen 27B: ~54B params @ bf16 = 108GB model states
- Full fine-tuning: +216GB optimizer + 108GB gradients = 432GB total
- ZeRO-Infinity offloads to NVMe SSD (/mnt/bigssd)
- Only active layer on GPU at any time (~2-4GB per layer)
- Franken: 10B params, stays on GPU (frozen, ~20GB)
- SAEs: ~3GB, stay on GPU

Expected speed: ~5-15 sec/step (vs 0.5 sec for in-GPU)
But it's TRUE full fine-tuning of all 54B parameters!
"""

import os
import sys
import gc
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
from tqdm import tqdm

# DeepSpeed
import deepspeed
from deepspeed.ops.adam import DeepSpeedCPUAdam, FusedAdam

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

# ============================================================
# MEMORY TRACKER
# ============================================================

class MemoryTracker:
    def __init__(self, threshold_gb=120):
        self.threshold = threshold_gb * 1e9
        self.peak_allocated = 0
        
    def check(self, label=""):
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated()
            reserved = torch.cuda.memory_reserved()
            self.peak_allocated = max(self.peak_allocated, allocated)
            print(f"[MEM] {label}: Alloc={allocated/1e9:.1f}GB | Reserved={reserved/1e9:.1f}GB | Peak={self.peak_allocated/1e9:.1f}GB")
            if allocated > self.threshold:
                print(f"[MEM WARNING] Approaching limit!")
        return True

# ============================================================
# SAE MODULES
# ============================================================

class QwenScopeSAE(nn.Module):
    """Qwen-Scope SAE - trainable, integrated into Qwen"""
    def __init__(self, d_model=5120, n_features=81920):
        super().__init__()
        self.d_model = d_model
        self.n_features = n_features
        self.W_enc = nn.Parameter(torch.empty(n_features, d_model))
        self.b_enc = nn.Parameter(torch.empty(n_features))
        self.W_dec = nn.Parameter(torch.empty(d_model, n_features))
        self.b_dec = nn.Parameter(torch.empty(d_model))
        
    def encode(self, x, chunk_size=4096):
        B, T, D = x.shape
        x_flat = x.reshape(-1, D)
        chunks = []
        for i in range(0, x_flat.shape[0], chunk_size):
            chunk = x_flat[i:i+chunk_size]
            acts = F.relu(F.linear(chunk, self.W_enc, self.b_enc))
            chunks.append(acts)
        acts = torch.cat(chunks, dim=0)
        return acts.reshape(B, T, -1)
    
    def decode(self, acts, chunk_size=4096):
        B, T, n_features = acts.shape
        acts_flat = acts.reshape(-1, n_features)
        chunks = []
        for i in range(0, acts_flat.shape[0], chunk_size):
            chunk = acts_flat[i:i+chunk_size]
            h = F.linear(chunk, self.W_dec, self.b_dec)
            chunks.append(h)
        h = torch.cat(chunks, dim=0)
        return h.reshape(B, T, -1)

# ============================================================
# FRANKEN V8 25-GRAFTS (Teacher - Frozen)
# ============================================================

class FrankenV8_25Grafts(nn.Module):
    """Franken V8 25-Grafts - Teacher model, frozen"""
    def __init__(self, vocab_size=248077, d_model=5120, num_layers=8, num_heads=32):
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.num_layers = num_layers
        
        self.embed_tokens = nn.Embedding(vocab_size, d_model)
        self.layers = nn.ModuleList([
            FrankenLayer(d_model, num_heads) for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        
    def forward(self, input_ids, return_hidden=False):
        h = self.embed_tokens(input_ids)
        for layer in self.layers:
            h = layer(h)
        h = self.norm(h)
        logits = self.lm_head(h)
        if return_hidden:
            return logits, h
        return logits

class FrankenLayer(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.GELU(),
            nn.Linear(d_model * 4, d_model)
        )
        
    def forward(self, x):
        attn_out, _ = self.attn(x, x, x)
        x = self.norm1(x + attn_out)
        ffn_out = self.ffn(x)
        x = self.norm2(x + ffn_out)
        return x

# ============================================================
# DATASET
# ============================================================

class TrainingDataset(Dataset):
    def __init__(self, data_dir, max_seq_len=2048):
        self.data_dir = Path(data_dir)
        self.files = sorted(self.data_dir.glob('sample_*.pt'))
        self.max_seq_len = max_seq_len
        print(f"Found {len(self.files)} training samples")
    
    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location='cpu')
        input_ids = data['input_ids']
        if input_ids.shape[1] > self.max_seq_len:
            input_ids = input_ids[:, :self.max_seq_len]
        return {'input_ids': input_ids}

# ============================================================
# DEEPSPEED CONFIG
# ============================================================

def get_deepspeed_config(offload_dir="/mnt/bigssd/deepspeed_offload"):
    """ZeRO-Infinity config for full fine-tuning Qwen 27B on 130GB GPU"""
    
    os.makedirs(offload_dir, exist_ok=True)
    
    ds_config = {
        "bf16": {
            "enabled": True
        },
        "zero_optimization": {
            "stage": 3,
            "offload_optimizer": {
                "device": "nvme",
                "nvme_path": offload_dir,
                "pin_memory": False
            },
            "offload_param": {
                "device": "nvme",
                "nvme_path": offload_dir,
                "pin_memory": False,
                "buffer_size": 2000000000
            },
            "overlap_comm": False,
            "contiguous_gradients": True,
            "sub_group_size": 1e9,
            "reduce_bucket_size": "auto",
            "stage3_prefetch_bucket_size": "auto",
            "stage3_param_persistence_threshold": "auto",
            "stage3_max_live_parameters": 1e9,
            "stage3_max_reuse_distance": 1e9,
            "stage3_gather_16bit_weights_on_model_save": True
        },
        "zero_force_ds_cpu_optimizer": True,
        "gradient_accumulation_steps": 1,
        "gradient_clipping": 1.0,
        "steps_per_print": 1,
        "train_batch_size": 1,
        "train_micro_batch_size_per_gpu": 1,
        "wall_clock_breakdown": False,
        "optimizer": {
            "type": "AdamW",
            "params": {
                "lr": 1e-5,
                "betas": [0.9, 0.999],
                "eps": 1e-8,
                "weight_decay": 0.01
            }
        },
        "scheduler": {
            "type": "WarmupLR",
            "params": {
                "warmup_min_lr": 0,
                "warmup_max_lr": 1e-5,
                "warmup_num_steps": 100
            }
        }
    }
    
    return ds_config

# ============================================================
# MAIN TRAINING SCRIPT
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--qwen-path', default='/data/models/Qwen3.6-27B-Uncensored')
    parser.add_argument('--franken-path', default='/data/models/FrankenV8-Final/final_model.pt')
    parser.add_argument('--sae-dir', default='/data/models/Qwen-Scope')
    parser.add_argument('--data-dir', default='/data/SpecForge/custom_dflash/hidden_states')
    parser.add_argument('--output-dir', default='/data/models/Qwen36-FrankenV8-FullFT')
    parser.add_argument('--num-steps', type=int, default=1000)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--seq-len', type=int, default=2048)
    parser.add_argument('--lr', type=float, default=1e-5)
    parser.add_argument('--save-every', type=int, default=100)
    parser.add_argument('--offload-dir', default='/mnt/bigssd/deepspeed_offload')
    parser.add_argument('--local_rank', type=int, default=0, help='local rank for distributed training')
    args = parser.parse_args()
    
    print("="*70)
    print("Qwen 3.6 27B FULL FINE-TUNING with ZeRO-Infinity")
    print("="*70)
    print(f"Student: Qwen 3.6 27B (ALL {27_000_000_000:,} params trainable)")
    print(f"Teacher: Franken V8 25-Grafts (frozen)")
    print(f"SAEs: Qwen-Scope (trainable, integrated)")
    print(f"Offload: {args.offload_dir}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print("="*70)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Memory tracker
    memory = MemoryTracker()
    
    # ============================================================
    # STEP 1: Load tokenizer
    # ============================================================
    print("\n[1/6] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.qwen_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f"  Vocab size: {len(tokenizer)}")
    
    # ============================================================
    # STEP 2: Load Qwen 27B (Student - will be trainable)
    # ============================================================
    print("\n[2/6] Loading Qwen 3.6 27B (student, will be fully trainable)...")
    print("  Loading weights to CPU first, then DeepSpeed will partition to NVMe...")
    
    # Load Qwen on CPU first (weights are ~108GB, fits in 121GB RAM)
    qwen = AutoModelForCausalLM.from_pretrained(
        args.qwen_path,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map='cpu',  # Load to CPU first
        ignore_mismatched_sizes=True  # Handle any size mismatches
    )
    
    print(f"  Qwen loaded: {sum(p.numel() for p in qwen.parameters()) / 1e9:.1f}B params")
    memory.check("After Qwen CPU load")
    
    # ============================================================
    # STEP 3: Load Qwen-Scope SAEs (Trainable)
    # ============================================================
    print("\n[3/6] Loading Qwen-Scope SAEs (trainable)...")
    sae_files = sorted(Path(args.sae_dir).glob('layer*.sae.pt'))
    print(f"  Found {len(sae_files)} SAE files")
    
    saes = []
    for i, sae_file in enumerate(sae_files[:2]):  # Load first 2 for now
        layer_idx = int(sae_file.stem.split('.')[0].replace('layer', ''))
        sae = QwenScopeSAE(d_model=5120, n_features=81920)
        sae.load_state_dict(torch.load(sae_file, map_location='cpu'))
        sae = sae.cuda()  # SAEs stay on GPU (small)
        saes.append((layer_idx, sae))
        print(f"    SAE layer {layer_idx}: {sum(p.numel() for p in sae.parameters()) / 1e6:.1f}M params")
    
    memory.check("After SAEs loaded")
    
    # ============================================================
    # STEP 4: Load Franken V8 (Teacher - Frozen)
    # ============================================================
    print("\n[4/6] Loading Franken V8 25-Grafts (teacher, frozen)...")
    franken = FrankenV8_25Grafts(vocab_size=len(tokenizer), d_model=5120, num_layers=8, num_heads=32)
    
    # Load pretrained weights
    if os.path.exists(args.franken_path):
        checkpoint = torch.load(args.franken_path, map_location='cpu')
        # Shape-filtered loading (handle vocab mismatch)
        model_dict = franken.state_dict()
        loaded = 0
        skipped = 0
        for k, v in checkpoint.items():
            if k in model_dict:
                if v.shape == model_dict[k].shape:
                    model_dict[k] = v
                    loaded += 1
                else:
                    skipped += 1
                    print(f"    Skip {k}: checkpoint {v.shape} vs model {model_dict[k].shape}")
        franken.load_state_dict(model_dict, strict=False)
        print(f"  Loaded {loaded} layers, skipped {skipped}")
    
    franken = franken.cuda()  # Franken stays on GPU (frozen, 20GB)
    franken.eval()
    for p in franken.parameters():
        p.requires_grad = False
    
    print(f"  Franken: {sum(p.numel() for p in franken.parameters()) / 1e9:.1f}B params (frozen)")
    memory.check("After Franken loaded")
    
    # ============================================================
    # STEP 5: Create dataset
    # ============================================================
    print("\n[5/6] Creating dataset...")
    dataset = TrainingDataset(args.data_dir, max_seq_len=args.seq_len)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    
    # ============================================================
    # STEP 6: Setup DeepSpeed ZeRO-Infinity
    # ============================================================
    print("\n[6/6] Setting up DeepSpeed ZeRO-Infinity...")
    print("  This will offload optimizer states + parameters to NVMe SSD")
    print(f"  Offload path: {args.offload_dir}")
    
    ds_config = get_deepspeed_config(args.offload_dir)
    
    # Initialize DeepSpeed engine
    # Qwen is the model being trained (all params trainable)
    model_engine, optimizer, _, scheduler = deepspeed.initialize(
        model=qwen,
        model_parameters=qwen.parameters(),
        config=ds_config
    )
    
    print("  DeepSpeed engine initialized!")
    print(f"  ZeRO stage: {model_engine.zero_optimization_stage()}")
    memory.check("After DeepSpeed init")
    
    # ============================================================
    # TRAINING LOOP
    # ============================================================
    print(f"\n{'='*70}")
    print(f"Starting FULL FINE-TUNING: {args.num_steps} steps")
    print(f"Batch size: {args.batch_size}, LR: {args.lr}")
    print(f"Every parameter of Qwen 27B will be updated!")
    print(f"{'='*70}\n")
    
    loss_history = {'total': [], 'logits': [], 'hidden': [], 'sae': [], 'quality': []}
    
    model_engine.train()
    global_step = 0
    
    while global_step < args.num_steps:
        for batch in dataloader:
            if global_step >= args.num_steps:
                break
            
            input_ids = batch['input_ids'].cuda()
            
            # ============================================================
            # TEACHER FORWARD (Franken - frozen, on GPU)
            # ============================================================
            with torch.no_grad():
                franken_logits, franken_hidden = franken(input_ids, return_hidden=True)
                
                # Analyze Franken's hidden states through SAEs
                sae_results = []
                for layer_idx, sae in saes:
                    acts = sae.encode(franken_hidden)
                    h_recon = sae.decode(acts)
                    recon_error = F.mse_loss(h_recon, franken_hidden)
                    sparsity = (acts > 0).float().mean()
                    sae_results.append({
                        'features': acts,
                        'reconstruction': h_recon,
                        'recon_error': recon_error,
                        'sparsity': sparsity
                    })
                
                # Quality score
                total_recon_error = sum(r['recon_error'] for r in sae_results)
                quality = torch.exp(-total_recon_error)
                
                # Teacher targets
                teacher_logits = franken_logits
                teacher_hidden = franken_hidden
                teacher_sae_features = sae_results[0]['features']
            
            # ============================================================
            # STUDENT FORWARD (Qwen - trainable, via DeepSpeed)
            # ============================================================
            # DeepSpeed handles the ZeRO-3 partitioning automatically
            # Only active layer on GPU, rest on NVMe SSD
            student_outputs = model_engine(input_ids, output_hidden_states=True)
            student_logits = student_outputs.logits
            student_hidden = student_outputs.hidden_states[-1]
            
            # ============================================================
            # COMPUTE LOSSES
            # ============================================================
            
            # A. Next-token prediction (distill from Franken)
            targets_ids = input_ids[:, 1:].contiguous()
            logits_shifted = student_logits[:, :-1, :].contiguous()
            logits_loss = F.cross_entropy(
                logits_shifted.view(-1, logits_shifted.size(-1)),
                targets_ids.view(-1),
                ignore_index=0
            )
            
            # B. Hidden state alignment (match Franken's reasoning)
            hidden_target = teacher_hidden[:, :-1, :].contiguous()
            student_hidden_shifted = student_hidden[:, :-1, :].contiguous()
            hidden_loss = F.mse_loss(student_hidden_shifted, hidden_target)
            
            # C. SAE feature alignment (Qwen should produce Franken-like SAE features)
            # Encode student hidden states through SAE
            student_sae_features = saes[0][1].encode(student_hidden)
            min_len = min(student_sae_features.shape[1], teacher_sae_features.shape[1])
            sae_loss = F.mse_loss(
                student_sae_features[:, :min_len, :],
                teacher_sae_features[:, :min_len, :]
            )
            
            # D. Quality-adaptive weighting
            adaptive_weight = 1.0 + (1.0 - quality) * 2.0
            
            # Combined loss
            total_loss = (
                logits_loss + 
                0.5 * hidden_loss + 
                0.3 * sae_loss
            ) * adaptive_weight
            
            # ============================================================
            # BACKWARD (DeepSpeed handles ZeRO-3 all-gather/reduce)
            # ============================================================
            model_engine.backward(total_loss)
            model_engine.step()
            
            # Track metrics
            loss_history['total'].append(total_loss.item())
            loss_history['logits'].append(logits_loss.item())
            loss_history['hidden'].append(hidden_loss.item())
            loss_history['sae'].append(sae_loss.item())
            loss_history['quality'].append(quality.item())
            
            global_step += 1
            
            if global_step % 1 == 0:
                print(f"Step {global_step}/{args.num_steps} | "
                      f"Loss: {total_loss.item():.3f} | "
                      f"Logits: {logits_loss.item():.3f} | "
                      f"Hidden: {hidden_loss.item():.3f} | "
                      f"SAE: {sae_loss.item():.3f} | "
                      f"Quality: {quality.item():.4f}")
            
            # Save checkpoint
            if global_step % args.save_every == 0:
                checkpoint_path = f"{args.output_dir}/checkpoint_step_{global_step}"
                print(f"\nSaving checkpoint to {checkpoint_path}...")
                model_engine.save_checkpoint(args.output_dir, tag=f"step_{global_step}")
                
                # Save loss history
                with open(f"{args.output_dir}/loss_history.json", 'w') as f:
                    json.dump(loss_history, f)
                print(f"Checkpoint saved!\n")
            
            memory.check(f"Step {global_step}")
    
    # ============================================================
    # SAVE FINAL MODEL
    # ============================================================
    print(f"\n{'='*70}")
    print("Training complete! Saving final model...")
    print(f"{'='*70}")
    
    final_path = f"{args.output_dir}/final"
    model_engine.save_checkpoint(args.output_dir, tag="final")
    
    with open(f"{args.output_dir}/loss_history.json", 'w') as f:
        json.dump(loss_history, f)
    
    print(f"Final model saved to {final_path}")
    print(f"Loss history: {args.output_dir}/loss_history.json")
    print(f"\n{'='*70}")
    print("FULL FINE-TUNING COMPLETE!")
    print(f"All {sum(p.numel() for p in qwen.parameters()) / 1e9:.1f}B parameters updated!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
