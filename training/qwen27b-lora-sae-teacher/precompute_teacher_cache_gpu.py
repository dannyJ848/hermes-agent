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
import gc
from pathlib import Path
from datetime import datetime

import torch
import pyarrow.parquet as pq

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

sys.path.insert(0, '/data/SpecForge/custom_dflash')

from train_lora_sae_teacher_v1 import TrainConfig, AugmentedStreamingDataset
from franken_v8_bridge_v3 import FrankenV8Bridge

def precompute_teacher_cache_gpu(config):
    """Precompute teacher hidden states using GPU acceleration."""
    
    logging.info("=" * 70)
    logging.info("GPU-ACCELERATED TEACHER CACHE PRECOMPUTATION")
    logging.info("=" * 70)
    
    # Verify GPU
    if not torch.cuda.is_available():
        logging.error("CUDA not available. Falling back to CPU.")
        return False
    
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
    logging.info(f"GPU: {torch.cuda.get_device_name(0)} ({gpu_mem:.1f}GB)")
    
    # Initialize tokenizer
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(config.model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Initialize teacher on GPU
    logging.info("Loading Franken V8 teacher model to GPU...")
    teacher = FrankenV8Bridge(
        model_path=config.teacher_model_path,
        device="cuda",  # GPU!
        dtype=torch.bfloat16 if config.bf16 else torch.float32
    )
    
    if teacher.model is None:
        logging.error("Failed to load teacher model. Aborting.")
        return False
    
    # Log GPU memory after teacher load
    teacher_mem = torch.cuda.memory_allocated() / 1e9
    logging.info(f"Teacher loaded. GPU memory used: {teacher_mem:.1f}GB")
    
    # Create cache directory
    cache_dir = Path(config.teacher_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Load or create index
    index_path = cache_dir / "index.json"
    cache_index = {}
    if index_path.exists():
        with open(index_path, 'r') as f:
            cache_index = json.load(f)
        logging.info(f"Resuming: {len(cache_index)} samples already cached")
    
    # Create dataset (no teacher needed for generation)
    logging.info("Loading dataset...")
    dataset = AugmentedStreamingDataset(config, tokenizer, teacher=None)
    real_files = dataset.real_files
    logging.info(f"Found {len(real_files)} real data files")
    
    # Statistics
    total_samples = 0
    cached_samples = 0
    skipped_samples = 0
    error_samples = 0
    last_index_save = 0
    
    # Batch size for GPU processing
    batch_size = config.batch_size  # Use same batch as training
    
    for file_idx, file_path in enumerate(real_files):
        logging.info(f"Processing file {file_idx+1}/{len(real_files)}: {file_path}")
        
        try:
            table = pq.read_table(file_path)
            df = table.to_pandas()
            
            # Process in batches for GPU efficiency
            batch_texts = []
            batch_ids = []
            
            for row_idx, row in df.iterrows():
                sample_id = f"file{file_idx}_row{row_idx}"
                
                if sample_id in cache_index:
                    skipped_samples += 1
                    continue
                
                text = dataset._format_conversation(row.to_dict())
                if not text:
                    continue
                
                batch_texts.append(text)
                batch_ids.append(sample_id)
                
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
                    
                    # Save index every 10 batches (more frequent than before)
                    if cached_samples - last_index_save >= 50:
                        _save_index(index_path, cache_index)
                        last_index_save = cached_samples
                        logging.info(
                            f"  Progress: {total_samples} processed, "
                            f"{cached_samples} cached, {skipped_samples} skipped, "
                            f"{error_samples} errors"
                        )
            
            # Process remaining batch
            if batch_texts:
                _process_batch(
                    teacher, tokenizer, batch_texts, batch_ids,
                    cache_dir, cache_index, config
                )
                cached_samples += len(batch_texts)
                total_samples += len(batch_texts)
            
        except Exception as e:
            logging.error(f"Failed to process file {file_path}: {e}")
            continue
    
    # Final save
    _save_index(index_path, cache_index)
    
    logging.info("=" * 70)
    logging.info("PRECOMPUTATION COMPLETE")
    logging.info(f"Total samples processed: {total_samples}")
    logging.info(f"Cached: {cached_samples}")
    logging.info(f"Skipped: {skipped_samples}")
    logging.info(f"Errors: {error_samples}")
    logging.info(f"Cache directory: {cache_dir}")
    logging.info("=" * 70)
    
    return True


def _process_batch(teacher, tokenizer, texts, sample_ids, cache_dir, cache_index, config):
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
        
        # Move to CPU for saving
        if teacher_hidden:
            for i, sample_id in enumerate(sample_ids):
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
        for sample_id in sample_ids:
            cache_index[sample_id] = "ERROR"


def _save_index(index_path, cache_index):
    """Save index atomically."""
    temp_path = str(index_path) + ".tmp"
    with open(temp_path, 'w') as f:
        json.dump(cache_index, f)
    os.replace(temp_path, index_path)


if __name__ == "__main__":
    config = TrainConfig()
    
    if os.environ.get("TEACHER_CACHE_DIR"):
        config.teacher_cache_dir = os.environ.get("TEACHER_CACHE_DIR")
    
    success = precompute_teacher_cache_gpu(config)
    sys.exit(0 if success else 1)
