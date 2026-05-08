#!/usr/bin/env python3
"""
Precompute Teacher Hidden States Cache for Franken V8

This script runs BEFORE training to precompute all teacher hidden states
for the entire dataset, saving them to fast SSD. During training, the
main script loads these cached states instead of running the teacher model.

This eliminates the CPU bottleneck while maintaining full teacher distillation.

Usage:
    python3 precompute_teacher_cache.py

Output:
    /mnt/bigssd/teacher_cache/          # Pickled hidden state dicts
    /mnt/bigssd/teacher_cache/index.json # Mapping: sample_id -> cache_file

Time estimate: ~2-4 hours for full dataset (depends on CPU speed)
"""

import os
import sys
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

import torch
import torch.nn as nn

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train_lora_sae_teacher_v1 import (
    TrainConfig, TeacherModelWrapper, load_sae, get_sae_feature_acts,
    AugmentedStreamingDataset
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/mnt/bigssd/precompute_teacher_cache.log')
    ]
)


def precompute_teacher_cache(config: TrainConfig):
    """Precompute and cache teacher hidden states for all dataset samples."""
    
    logging.info("=" * 70)
    logging.info("TEACHER CACHE PRECOMPUTATION")
    logging.info("=" * 70)
    
    # Load tokenizer (use student tokenizer since teacher may not have one)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        config.student_model_path,
        trust_remote_code=True,
        padding_side="right"
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    # Load teacher model
    logging.info("Loading Franken V8 teacher model...")
    teacher = TeacherModelWrapper(config.teacher_model_path, device="cpu")
    
    if teacher.model is None:
        logging.error("Failed to load teacher model. Aborting.")
        return False
    
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
    
    # Create dataset
    logging.info("Loading dataset...")
    dataset = AugmentedStreamingDataset(config, tokenizer, teacher=None)  # No teacher for generation
    
    # Get all real files
    real_files = dataset.real_files
    logging.info(f"Found {len(real_files)} real data files")
    
    # Process each file
    total_samples = 0
    cached_samples = 0
    skipped_samples = 0
    error_samples = 0
    
    import pyarrow.parquet as pq
    
    for file_idx, file_path in enumerate(real_files):
        logging.info(f"Processing file {file_idx+1}/{len(real_files)}: {file_path}")
        
        try:
            # Read parquet file
            table = pq.read_table(file_path)
            df = table.to_pandas()
            
            # Process each row
            for row_idx, row in df.iterrows():
                sample_id = f"file{file_idx}_row{row_idx}"
                
                # Skip if already cached
                if sample_id in cache_index:
                    skipped_samples += 1
                    continue
                
                # Format conversation
                text = dataset._format_conversation(row.to_dict())
                if not text:
                    continue
                
                # Tokenize
                tokens = tokenizer(
                    text,
                    truncation=True,
                    max_length=config.max_seq_len,
                    return_tensors="pt"
                )
                input_ids = tokens['input_ids']
                
                # Compute teacher hidden states
                try:
                    with torch.no_grad():
                        teacher_hidden = teacher.get_hidden_states(
                            input_ids,
                            config.teacher_layers
                        )
                    
                    if not teacher_hidden:
                        error_samples += 1
                        continue
                    
                    # Save to cache
                    cache_path = cache_dir / f"{sample_id}.pkl"
                    with open(cache_path, 'wb') as f:
                        pickle.dump(teacher_hidden, f)
                    
                    cache_index[sample_id] = str(cache_path)
                    cached_samples += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to compute teacher states for {sample_id}: {e}")
                    error_samples += 1
                    continue
                
                total_samples += 1
                
                # Progress logging
                if total_samples % 100 == 0:
                    logging.info(
                        f"  Progress: {total_samples} processed, "
                        f"{cached_samples} cached, {skipped_samples} skipped, "
                        f"{error_samples} errors"
                    )
                    
                    # Save index periodically
                    with open(index_path, 'w') as f:
                        json.dump(cache_index, f)
                    
                    # Force garbage collection
                    import gc
                    gc.collect()
            
        except Exception as e:
            logging.error(f"Failed to process file {file_path}: {e}")
            continue
    
    # Final save
    with open(index_path, 'w') as f:
        json.dump(cache_index, f)
    
    logging.info("=" * 70)
    logging.info("PRECOMPUTATION COMPLETE")
    logging.info(f"Total samples processed: {total_samples}")
    logging.info(f"Cached: {cached_samples}")
    logging.info(f"Skipped (already cached): {skipped_samples}")
    logging.info(f"Errors: {error_samples}")
    logging.info(f"Cache directory: {cache_dir}")
    logging.info(f"Index file: {index_path}")
    logging.info("=" * 70)
    
    return True


if __name__ == "__main__":
    config = TrainConfig()
    
    # Allow override via env vars
    if os.environ.get("TEACHER_CACHE_DIR"):
        config.teacher_cache_dir = os.environ.get("TEACHER_CACHE_DIR")
    
    success = precompute_teacher_cache(config)
    sys.exit(0 if success else 1)
