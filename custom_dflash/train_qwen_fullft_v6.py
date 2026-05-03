#!/usr/bin/env python3
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
import glob
import time

MODEL_PATH = '/data/models/Qwen3.6-27B-Uncensored'
DATA_PATH = '/data/SpecForge/custom_dflash/hidden_states'
CHECKPOINT_DIR = '/data/SpecForge/custom_dflash/checkpoints'

BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
LR = 1e-5
MAX_STEPS = 1000
SAVE_EVERY = 100
LOG_EVERY = 10
MAX_SEQ_LEN = 512

class HiddenStateDataset(Dataset):
    def __init__(self, data_dir, max_len=512):
        self.files = sorted(glob.glob(f'{data_dir}/*.pt'))
        self.max_len = max_len
        print(f'Found {len(self.files)} hidden state files', flush=True)
    
    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location='cpu')
        input_ids = data['input_ids'].squeeze(0)
        if input_ids.shape[0] > self.max_len:
            input_ids = input_ids[:self.max_len]
        return {'input_ids': input_ids, 'labels': input_ids.clone()}

def collate_fn(batch):
    max_len = max(b['input_ids'].shape[0] for b in batch)
    input_ids = torch.stack([
        torch.cat([b['input_ids'], torch.zeros(max_len - b['input_ids'].shape[0], dtype=torch.long)]) 
        if b['input_ids'].shape[0] < max_len else b['input_ids']
        for b in batch
    ])
    labels = input_ids.clone()
    attention_mask = (input_ids != 0).long()
    return {'input_ids': input_ids, 'labels': labels, 'attention_mask': attention_mask}

def main():
    print('='*60, flush=True)
    print('QWEN 27B FULL FT', flush=True)
    print('='*60, flush=True)
    
    torch.cuda.init()
    device = torch.device('cuda:0')
    print(f'Device: {device}', flush=True)
    print(f'GPU: {torch.cuda.get_device_name(0)}', flush=True)
    print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB', flush=True)
    
    print('\nLoading student model...', flush=True)
    start = time.time()
    student = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map='auto',
    )
    load_time = time.time() - start
    print(f'Model loaded in {load_time:.1f}s', flush=True)
    
    student.gradient_checkpointing_enable()
    student.train()
    
    total_params = sum(p.numel() for p in student.parameters())
    trainable = sum(p.numel() for p in student.parameters() if p.requires_grad)
    print(f'Total params: {total_params/1e9:.1f}B', flush=True)
    print(f'Trainable: {trainable/1e9:.1f}B', flush=True)
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    print('\nCreating SGD optimizer...', flush=True)
    optimizer = torch.optim.SGD(student.parameters(), lr=LR, momentum=0.0)
    
    dataset = HiddenStateDataset(DATA_PATH, max_len=MAX_SEQ_LEN)
    dataloader = DataLoader(
        dataset, 
        batch_size=BATCH_SIZE,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
    )
    
    print('\nStarting training...', flush=True)
    print(f'Target steps: {MAX_STEPS}', flush=True)
    print(f'Effective batch size: {BATCH_SIZE * GRAD_ACCUM_STEPS}', flush=True)
    print(f'Learning rate: {LR}', flush=True)
    print('-' * 60, flush=True)
    
    global_step = 0
    optimizer.zero_grad()
    step_start = time.time()
    
    for epoch in range(1000):
        for batch_idx, batch in enumerate(dataloader):
            if global_step >= MAX_STEPS:
                break
            
            input_ids = batch['input_ids'].to(student.device)
            labels = batch['labels'].to(student.device)
            attention_mask = batch['attention_mask'].to(student.device)
            
            outputs = student(
                input_ids=input_ids,
                labels=labels,
                attention_mask=attention_mask,
            )
            loss = outputs.loss / GRAD_ACCUM_STEPS
            
            loss.backward()
            
            if (batch_idx + 1) % GRAD_ACCUM_STEPS == 0:
                torch.nn.utils.clip_grad_norm_(student.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad()
                global_step += 1
                
                if global_step % LOG_EVERY == 0:
                    elapsed = time.time() - step_start
                    steps_per_sec = LOG_EVERY / elapsed
                    gpu_mem = torch.cuda.memory_allocated() / 1e9
                    loss_val = loss.item() * GRAD_ACCUM_STEPS
                    print(f'Step {global_step:4d} | Loss: {loss_val:.4f} | GPU: {gpu_mem:.1f}GB | {steps_per_sec:.2f} steps/s', flush=True)
                    step_start = time.time()
                
                if global_step % SAVE_EVERY == 0:
                    save_path = f'{CHECKPOINT_DIR}/step_{global_step}.pt'
                    torch.save(student.state_dict(), save_path)
                    print(f'Saved checkpoint: {save_path}', flush=True)
        
        if global_step >= MAX_STEPS:
            break
    
    final_path = f'{CHECKPOINT_DIR}/final.pt'
    torch.save(student.state_dict(), final_path)
    print(f'\nTraining complete! Final model: {final_path}', flush=True)
    print(f'Total steps: {global_step}', flush=True)

if __name__ == '__main__':
    main()
