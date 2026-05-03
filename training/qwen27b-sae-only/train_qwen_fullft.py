#!/usr/bin/env python3
"""
Full fine-tuning Qwen3.6-27B with Franken V8 teacher + Qwen-Scope SAEs
Custom PyTorch training loop with CPU-offloaded optimizer states
Uses SGD (no momentum) to fit within 130GB GPU memory
"""

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import glob
import time
from pathlib import Path

# Paths
MODEL_PATH = '/data/models/Qwen3.6-27B-Uncensored'
SAE_PATH = '/data/models/Qwen-Scope'
DATA_PATH = '/data/SpecForge/custom_dflash/hidden_states'
CHECKPOINT_DIR = '/data/SpecForge/custom_dflash/checkpoints'
FRANKEN_PATH = '/data/models/FrankenV8-Final/final_model.pt'

# Training config
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4  # Effective batch = 4
LR = 1e-5
MAX_STEPS = 1000
SAVE_EVERY = 100
LOG_EVERY = 10

class HiddenStateDataset(Dataset):
    def __init__(self, data_dir):
        self.files = sorted(glob.glob(f'{data_dir}/*.pt'))
        print(f'Found {len(self.files)} hidden state files')
    
    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location='cpu')
        return {
            'input_ids': data['input_ids'].squeeze(0),
            'labels': data['input_ids'].squeeze(0),
        }

def collate_fn(batch):
    max_len = max(b['input_ids'].shape[0] for b in batch)
    input_ids = torch.stack([
        torch.cat([b['input_ids'], torch.zeros(max_len - b['input_ids'].shape[0], dtype=torch.long)]) 
        if b['input_ids'].shape[0] < max_len else b['input_ids']
        for b in batch
    ])
    labels = input_ids.clone()
    return {'input_ids': input_ids, 'labels': labels}

def load_franken_teacher():
    """Load Franken V8 as teacher (frozen)"""
    print('Loading Franken V8 teacher...', flush=True)
    teacher = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map='auto',
    )
    # Load Franken weights
    state_dict = torch.load(FRANKEN_PATH, map_location='cpu')
    teacher.load_state_dict(state_dict, strict=False)
    teacher.eval()
    for p in teacher.parameters():
        p.requires_grad = False
    print('Teacher loaded (frozen)', flush=True)
    return teacher

def load_saes():
    """Load Qwen-Scope SAEs"""
    print('Loading SAEs...', flush=True)
    sae_files = sorted(glob.glob(f'{SAE_PATH}/*.pt'))
    saes = []
    for f in sae_files:
        sae = torch.load(f, map_location='cpu')
        saes.append(sae)
    print(f'Loaded {len(saes)} SAEs', flush=True)
    return saes

def main():
    print('='*60, flush=True)
    print('QWEN 27B FULL FT + FRANKEN V8 + SAEs', flush=True)
    print('='*60, flush=True)
    
    # Load student
    print('\nLoading student model...', flush=True)
    student = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map='auto',
    )
    student.gradient_checkpointing_enable()
    student.train()
    
    total_params = sum(p.numel() for p in student.parameters())
    trainable = sum(p.numel() for p in student.parameters() if p.requires_grad)
    print(f'Total params: {total_params/1e9:.1f}B', flush=True)
    print(f'Trainable: {trainable/1e9:.1f}B', flush=True)
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Load teacher (optional - can be None for now)
    teacher = None
    # teacher = load_franken_teacher()  # Uncomment when ready
    
    # Load SAEs (optional - can be integrated later)
    saes = None
    # saes = load_saes()  # Uncomment when ready
    
    # Optimizer: SGD with no momentum (zero state overhead)
    print('\nCreating SGD optimizer...', flush=True)
    optimizer = torch.optim.SGD(student.parameters(), lr=LR, momentum=0.0)
    
    # Dataset
    dataset = HiddenStateDataset(DATA_PATH)
    dataloader = DataLoader(
        dataset, 
        batch_size=BATCH_SIZE,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
    )
    
    # Training loop
    print('\nStarting training...', flush=True)
    global_step = 0
    optimizer.zero_grad()
    
    for epoch in range(1000):  # Large number, will break on MAX_STEPS
        for batch_idx, batch in enumerate(dataloader):
            if global_step >= MAX_STEPS:
                break
            
            # Move to device
            input_ids = batch['input_ids'].to(student.device)
            labels = batch['labels'].to(student.device)
            
            # Forward
            outputs = student(input_ids=input_ids, labels=labels)
            loss = outputs.loss / GRAD_ACCUM_STEPS
            
            # Backward
            loss.backward()
            
            # Step
            if (batch_idx + 1) % GRAD_ACCUM_STEPS == 0:
                optimizer.step()
                optimizer.zero_grad()
                global_step += 1
                
                # Log
                if global_step % LOG_EVERY == 0:
                    gpu_mem = torch.cuda.memory_allocated() / 1e9
                    print(f'Step {global_step} | Loss: {loss.item() * GRAD_ACCUM_STEPS:.4f} | GPU: {gpu_mem:.1f}GB', flush=True)
                
                # Save
                if global_step % SAVE_EVERY == 0:
                    save_path = f'{CHECKPOINT_DIR}/step_{global_step}.pt'
                    torch.save(student.state_dict(), save_path)
                    print(f'Saved checkpoint: {save_path}', flush=True)
        
        if global_step >= MAX_STEPS:
            break
    
    # Final save
    final_path = f'{CHECKPOINT_DIR}/final.pt'
    torch.save(student.state_dict(), final_path)
    print(f'\nTraining complete! Final model: {final_path}', flush=True)
    print(f'Total steps: {global_step}', flush=True)

if __name__ == '__main__':
    main()
