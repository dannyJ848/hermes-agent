#!/usr/bin/env python3
"""
Triple-Batch Franken v8 Training Pipeline

Splits 9999 samples into 3 batches of 3333 samples each.
Each batch: generate target_logits → train → save checkpoint → cleanup → repeat.

This fits within 3.7TB disk by never having more than one batch on disk at a time.
"""

import os
import sys
import argparse
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# ============================================================
# CONFIG
# ============================================================

TOTAL_SAMPLES = 9999
BATCH_SIZE = 3333
NUM_BATCHES = 3

BATCH_RANGES = [
    (0, 3333),      # Batch 1: samples 0-3332
    (3333, 6666),   # Batch 2: samples 3333-6665
    (6666, 9999),   # Batch 3: samples 6666-9998
]

# Paths
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states_full"
TARGET_MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored"
TRAIN_SCRIPT = "/data/SpecForge/custom_dflash/train_franken_v8_vllm_compatible.py"

# ============================================================
# LOGGING
# ============================================================

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

# ============================================================
# PHASE 1: GENERATE TARGET_LOGITS FOR A BATCH
# ============================================================

def generate_batch_logits(batch_id, start_idx, end_idx, output_dir, bf16=True):
    """Generate target_logits for a batch of samples."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    log(f"=== BATCH {batch_id}: Generating logits for samples {start_idx}-{end_idx-1} ===")
    log(f"Output directory: {output_dir}")
    
    # Check which samples already exist
    existing = set()
    for f in Path(output_dir).glob("*.pt"):
        try:
            # Extract sample index from filename
            idx = int(f.stem.split("_")[-1])
            existing.add(idx)
        except:
            pass
    
    if existing:
        log(f"Found {len(existing)} existing samples, will skip them")
    
    # Load target model
    log("Loading target model...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    dtype = torch.bfloat16 if bf16 else torch.float32
    
    model = AutoModelForCausalLM.from_pretrained(
        TARGET_MODEL_PATH,
        torch_dtype=dtype,
        device_map='auto',
        trust_remote_code=True,
        attn_implementation='eager',
    )
    model.eval()
    
    tokenizer = AutoTokenizer.from_pretrained(TARGET_MODEL_PATH, trust_remote_code=True)
    log(f"Model loaded. Vocab size: {len(tokenizer)}")
    
    # Generate logits for each sample
    generated = 0
    skipped = 0
    errors = 0
    
    for i in tqdm(range(start_idx, end_idx), desc=f"Batch {batch_id}"):
        input_file = Path(HIDDEN_STATES_DIR) / f"sample_{i:06d}.pt"
        output_file = Path(output_dir) / f"sample_{i:06d}.pt"
        
        if i in existing:
            skipped += 1
            continue
        
        if not input_file.exists():
            log(f"WARNING: {input_file} not found, skipping")
            errors += 1
            continue
        
        try:
            # Load input data
            data = torch.load(input_file, map_location='cpu')
            input_ids = data['input_ids']
            hidden_states = data['hidden_states']
            seq_len = data['seq_len']
            
            # Generate target_logits
            with torch.no_grad():
                input_ids_batch = input_ids.unsqueeze(0).to(device)
                outputs = model(input_ids_batch, output_hidden_states=False)
                target_logits = outputs.logits[0].cpu()
            
            # Save with logits
            output_data = {
                'input_ids': input_ids,
                'hidden_states': hidden_states,
                'target_logits': target_logits,
                'seq_len': seq_len,
            }
            
            torch.save(output_data, output_file)
            generated += 1
            
            # Clear cache periodically
            if generated % 100 == 0:
                torch.cuda.empty_cache()
                log(f"Generated {generated} samples this batch ({skipped} skipped, {errors} errors)")
                
        except Exception as e:
            log(f"ERROR processing sample {i}: {e}")
            errors += 1
            continue
    
    # CRITICAL: Aggressive cleanup to free GPU memory before training
    log("Unloading target model and freeing GPU memory...")
    del model
    del tokenizer
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        log(f"GPU memory after cleanup: {torch.cuda.memory_allocated()/1e9:.2f}GB")
    
    log(f"=== BATCH {batch_id} GENERATION COMPLETE ===")
    log(f"Generated: {generated}, Skipped: {skipped}, Errors: {errors}")
    log(f"Total samples in batch: {len(list(Path(output_dir).glob('*.pt')))}")
    
    return generated > 0

# ============================================================
# PHASE 2: TRAIN FRANKEN V8 ON A BATCH
# ============================================================

def train_franken_v8(batch_id, logits_dir, output_dir, resume_from=None, max_steps=10000):
    """Train Franken v8 on a batch of target_logits."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    log(f"=== BATCH {batch_id}: Training Franken v8 ===")
    log(f"Logits directory: {logits_dir}")
    log(f"Output directory: {output_dir}")
    
    # Build training command
    cmd = [
        "python3", TRAIN_SCRIPT,
        "--hidden-states-dir", logits_dir,
        "--output-dir", output_dir,
        "--max-steps", str(max_steps),
        "--batch-size", "4",
        "--grad-accum", "2",
        "--bf16",
        "--save-interval", "500",
        "--log-interval", "10",
    ]
    
    if resume_from and os.path.exists(resume_from):
        cmd.extend(["--resume-from", resume_from])
        log(f"Resuming from: {resume_from}")
    
    log(f"Training command: {' '.join(cmd)}")
    
    # Run training
    # Pre-train cleanup: ensure no GPU memory leakage from previous phase
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        log(f"Pre-training GPU state: {torch.cuda.memory_allocated()/1e9:.2f}GB allocated")
    
    import subprocess
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        log(f"ERROR: Training failed with return code {result.returncode}")
        return False
    
    log(f"=== BATCH {batch_id} TRAINING COMPLETE ===")
    return True

# ============================================================
# PHASE 3: CLEANUP
# ============================================================

def cleanup_batch_logits(logits_dir):
    """Delete batch logits to free disk space."""
    log(f"Cleaning up: {logits_dir}")
    
    if os.path.exists(logits_dir):
        import shutil
        shutil.rmtree(logits_dir)
        log(f"Deleted {logits_dir}")
    
    # Verify disk space
    stat = os.statvfs("/")
    free_gb = stat.f_bavail * stat.f_frsize / (1024**3)
    log(f"Disk free: {free_gb:.1f} GB")

# ============================================================
# MAIN PIPELINE
# ============================================================

def run_triple_batch_pipeline(start_batch=1):
    """Run the complete triple-batch pipeline."""
    
    log("=" * 70)
    log("FRANKEN v8 TRIPLE-BATCH PIPELINE")
    log("=" * 70)
    log(f"Total samples: {TOTAL_SAMPLES}")
    log(f"Batches: {NUM_BATCHES} x {BATCH_SIZE} samples")
    log(f"Target model: {TARGET_MODEL_PATH}")
    log(f"Training script: {TRAIN_SCRIPT}")
    
    # Check prerequisites
    if not os.path.exists(HIDDEN_STATES_DIR):
        log(f"ERROR: Hidden states directory not found: {HIDDEN_STATES_DIR}")
        return False
    
    if not os.path.exists(TARGET_MODEL_PATH):
        log(f"ERROR: Target model not found: {TARGET_MODEL_PATH}")
        return False
    
    if not os.path.exists(TRAIN_SCRIPT):
        log(f"ERROR: Training script not found: {TRAIN_SCRIPT}")
        return False
    
    # Check disk space
    stat = os.statvfs("/")
    free_gb = stat.f_bavail * stat.f_frsize / (1024**3)
    log(f"Current disk free: {free_gb:.1f} GB")
    
    if free_gb < 500:
        log("WARNING: Less than 500GB free. May need to clean up first.")
    
    # Process each batch
    last_checkpoint = None
    
    for batch_id in range(start_batch, NUM_BATCHES + 1):
        start_idx, end_idx = BATCH_RANGES[batch_id - 1]
        
        log("")
        log("=" * 70)
        log(f"BATCH {batch_id}/{NUM_BATCHES}: samples {start_idx}-{end_idx-1}")
        log("=" * 70)
        
        # Directories for this batch
        logits_dir = f"/data/SpecForge/custom_dflash/batch_{batch_id}_logits"
        train_output = f"/data/models/FrankenV8-Batch{batch_id}"
        
        # Phase 1: Generate logits (runs in separate process to isolate memory)
        log("PHASE 1: Generating target_logits...")
        import subprocess
        gen_cmd = [
            sys.executable, "-c",
            "import sys; sys.path.insert(0, '/data/SpecForge/custom_dflash'); "
            "from triple_batch_pipeline import generate_batch_logits; "
            "import torch; "
            "success = generate_batch_logits(" + str(batch_id) + ", " + str(start_idx) + ", " + str(end_idx) + ", '" + logits_dir + "'); "
            "sys.exit(0 if success else 1)"
        ]
        log("Starting logits generation subprocess...")
        gen_result = subprocess.run(gen_cmd, capture_output=False, text=True)
        
        if gen_result.returncode != 0:
            log(f"ERROR: Failed to generate logits for batch {batch_id}")
            return False
        
        log("Logits generation complete. Target model fully unloaded.")
        
        # Phase 2: Train (runs in separate process with fresh memory)
        log("PHASE 2: Training Franken v8...")
        train_cmd = [
            sys.executable, TRAIN_SCRIPT,
            "--hidden-states-dir", logits_dir,
            "--output-dir", train_output,
            "--max-steps", "10000",
            "--batch-size", "4",
            "--grad-accum", "2",
            "--bf16",
            "--save-interval", "500",
            "--log-interval", "10",
        ]
        if last_checkpoint and os.path.exists(last_checkpoint):
            train_cmd.extend(["--resume-from", last_checkpoint])
        
        log("Starting training subprocess...")
        train_result = subprocess.run(train_cmd, capture_output=False, text=True)
        
        if train_result.returncode != 0:
            log(f"ERROR: Training failed for batch {batch_id}")
            return False
        
        # Update checkpoint for next batch
        last_checkpoint = os.path.join(train_output, "final_model.pt")
        if not os.path.exists(last_checkpoint):
            # Try to find latest checkpoint
            checkpoints = list(Path(train_output).glob("checkpoint-*.pt"))
            if checkpoints:
                last_checkpoint = str(sorted(checkpoints)[-1])
        
        # Phase 3: Cleanup (keep last batch's logits if it's the final batch)
        if batch_id < NUM_BATCHES:
            log("PHASE 3: Cleaning up batch logits...")
            cleanup_batch_logits(logits_dir)
        else:
            log("Final batch — keeping logits for potential continued training")
        
        log(f"BATCH {batch_id} COMPLETE. Checkpoint: {last_checkpoint}")
    
    # Final summary
    log("")
    log("=" * 70)
    log("ALL BATCHES COMPLETE")
    log("=" * 70)
    log(f"Final model: {last_checkpoint}")
    
    # Save pipeline status
    status = {
        "completed": True,
        "batches_done": NUM_BATCHES,
        "final_checkpoint": last_checkpoint,
        "timestamp": datetime.now().isoformat(),
    }
    
    status_file = "/data/SpecForge/custom_dflash/triple_batch_status.json"
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    log(f"Status saved to: {status_file}")
    
    return True

# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Triple-Batch Franken v8 Training')
    parser.add_argument('--start-batch', type=int, default=1, help='Start from batch N (1-3)')
    parser.add_argument('--generate-only', action='store_true', help='Only generate logits, skip training')
    parser.add_argument('--train-only', action='store_true', help='Only train, skip generation (logits must exist)')
    parser.add_argument('--logits-dir', type=str, help='Directory with pre-generated logits (for --train-only)')
    parser.add_argument('--output-dir', type=str, help='Training output directory (for --train-only)')
    args = parser.parse_args()
    
    if args.generate_only and args.train_only:
        print("ERROR: Cannot use both --generate-only and --train-only")
        return 1
    
    if args.train_only:
        if not args.logits_dir or not args.output_dir:
            print("ERROR: --train-only requires --logits-dir and --output-dir")
            return 1
        
        batch_id = args.start_batch
        success = train_franken_v8(batch_id, args.logits_dir, args.output_dir)
        return 0 if success else 1
    
    if args.generate_only:
        batch_id = args.start_batch
        start_idx, end_idx = BATCH_RANGES[batch_id - 1]
        logits_dir = f"/data/SpecForge/custom_dflash/batch_{batch_id}_logits"
        success = generate_batch_logits(batch_id, start_idx, end_idx, logits_dir)
        return 0 if success else 1
    
    # Full pipeline
    success = run_triple_batch_pipeline(args.start_batch)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
