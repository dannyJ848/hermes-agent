#!/usr/bin/env python3
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
import glob
import time

MODEL_PATH = '/data/models/Qwen3.6-27B-Uncensored'
DATA_PATH = '/data/SpecForge/custom_dflash/hidden_states'
CHECKPOINT_DIR = '/data/SpecForge/custom_dflash/checkpoints'
FRANKEN_PATH = '/data/models/FrankenV8-Final/final_model.pt'

BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
LR = 1e-5
MAX_STEPS = 1000
SAVE_EVERY = 100
LOG_EVERY = 10
MAX_SEQ_LEN = 512

USE_TEACHER = True
TEACHER_WEIGHT = 0.5

MAX_MEMORY = {0: '120GiB', 'cpu': '0GiB'}

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

def load_franken_teacher():
    print('Loading Franken V8 teacher on CPU...', flush=True)
    teacher = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map=None,
        low_cpu_mem_usage=True,
    )
    teacher = teacher.to('cpu')
    
    if os.path.exists(FRANKEN_PATH):
        print(f'Loading Franken weights from {FRANKEN_PATH}', flush=True)
        state_dict = torch.load(FRANKEN_PATH, map_location='cpu')
        model_dict = teacher.state_dict()
        filtered_dict = {k: v for k, v in state_dict.items() if k in model_dict and v.shape == model_dict[k].shape}
        print(f'Loading {len(filtered_dict)}/{len(state_dict)} Franken weights', flush=True)
        model_dict.update(filtered_dict)
        teacher.load_state_dict(model_dict)
        print('Franken weights loaded', flush=True)
    else:
        print(f'Franken weights not found, using base model', flush=True)
    
    teacher.eval()
    for p in teacher.parameters():
        p.requires_grad = False
    print('Teacher loaded (frozen, on CPU)', flush=True)
    return teacher

def compute_distillation_loss(student_logits, teacher_logits, temperature=2.0):
    student_probs = F.log_softmax(student_logits / temperature, dim=-1)
    teacher_probs = F.softmax(teacher_logits / temperature, dim=-1)
    kl_loss = F.kl_div(student_probs, teacher_probs, reduction='batchmean') * (temperature ** 2)
    return kl_loss

def main():
    print('='*60, flush=True)
    print('QWEN 27B FULL FT + FRANKEN V8 + SAEs', flush=True)
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
        max_memory=MAX_MEMORY,
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
    
    teacher = None
    if USE_TEACHER:
        try:
            teacher = load_franken_teacher()
        except Exception as e:
            print(f'Failed to load teacher: {e}', flush=True)
            teacher = None
    
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
    print(f'Teacher distillation: {USE_TEACHER and teacher is not None}', flush=True)
    print('-' * 60, flush=True)
    
    global_step = 0
    optimizer.zero_grad()
    step_start = time.time()
    
    for epoch in range(1000):
        for batch_idx, batch in enumerate(dataloader):
            if global_step >= MAX_STEPS:
                break
            
            input_ids = batch['input_ids'].to(device)
            labels = batch['labels'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            student_outputs = student(
                input_ids=input_ids,
                labels=labels,
                attention_mask=attention_mask,
            )
            loss = student_outputs.loss / GRAD_ACCUM_STEPS
            
            distill_loss_val = 0.0
            if teacher is not None:
                with torch.no_grad():
                    teacher_input_ids = input_ids.to('cpu')
                    teacher_attention_mask = attention_mask.to('cpu')
                    teacher_outputs = teacher(
                        input_ids=teacher_input_ids,
                        attention_mask=teacher_attention_mask,
                    )
                    teacher_logits = teacher_outputs.logits.to(device)
                
                student_logits = student_outputs.logits
                distill_loss = compute_distillation_loss(student_logits, teacher_logits)
                loss = loss + (TEACHER_WEIGHT * distill_loss / GRAD_ACCUM_STEPS)
                distill_loss_val = distill_loss.item()
            
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
                    log_str = f'Step {global_step:4d} | Loss: {loss_val:.4f} | GPU: {gpu_mem:.1f}GB | {steps_per_sec:.2f} steps/s'
                    if teacher is not None:
                        log_str += f' | Distill: {distill_loss_val:.4f}'
                    print(log_str, flush=True)
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
