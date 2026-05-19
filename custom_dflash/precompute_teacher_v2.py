#!/usr/bin/env python3
import os, time, glob, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

TEACHER_PATH = '/data/models/FrankenV8-Final/'
HIDDEN_STATES_DIR = '/data/SpecForge/custom_dflash/hidden_states/'
OUTPUT_DIR = '/mnt/bigssd/teacher_outputs_all/'
MAX_SEQ_LEN = 256

device = torch.device('cuda:0')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    t = time.strftime('%H:%M:%S')
    print(f'[{t}] {msg}', flush=True)

log('Loading teacher tokenizer...')
tokenizer = AutoTokenizer.from_pretrained(TEACHER_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

log('Loading teacher config...')
config = AutoConfig.from_pretrained(TEACHER_PATH, trust_remote_code=True)
config.vocab_size = len(tokenizer)
config.use_cache = False
log(f'Config: {config.model_type}, layers={config.num_hidden_layers}, hidden={config.hidden_size}')

log('Creating teacher model architecture...')
teacher = AutoModelForCausalLM.from_config(config, trust_remote_code=True)

log('Loading teacher weights from checkpoint...')
ckpt = torch.load('/data/models/FrankenV8-Final/final_model.pt', map_location='cpu')
teacher.load_state_dict(ckpt['model_state_dict'])
teacher = teacher.to(device).bfloat16()
teacher.eval()
log(f'Teacher loaded. Step: {ckpt.get("step", 0)}, Epoch: {ckpt.get("epoch", 0)}')

files = sorted(glob.glob(os.path.join(HIDDEN_STATES_DIR, '*.pt')))
log(f'Found {len(files)} samples')

for idx, fpath in enumerate(files):
    out_path = os.path.join(OUTPUT_DIR, f'teacher_logits_{idx:04d}.pt')
    if os.path.exists(out_path):
        log(f'  [{idx+1}/{len(files)}] Already exists, skipping')
        continue
    
    data = torch.load(fpath, map_location='cpu', weights_only=False)
    input_ids = data['input_ids'].squeeze(0)[:MAX_SEQ_LEN].unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = teacher(input_ids=input_ids)
        logits = outputs.logits.cpu().float()
    
    torch.save({'logits': logits, 'file_idx': idx}, out_path)
    log(f'  [{idx+1}/{len(files)}] Saved | Shape: {logits.shape}')

log('All teacher outputs computed!')
