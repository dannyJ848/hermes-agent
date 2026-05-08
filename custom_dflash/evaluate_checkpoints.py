#!/usr/bin/env python3
"""
Evaluate Qwen 27B checkpoints: standard vs novel architecture
Compares perplexity on held-out samples
"""
import os, sys, time, glob, torch, math
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

MODEL_PATH = '/data/models/Qwen3.6-27B-Uncensored/'
HIDDEN_STATES_DIR = '/data/SpecForge/custom_dflash/hidden_states/'
CHECKPOINT_DIR = '/data/SpecForge/custom_dflash/checkpoints/'
RESULTS_FILE = '/mnt/bigssd/evaluation_results.txt'

MAX_SEQ_LEN = 256
BATCH_SIZE = 1
EVAL_SAMPLES = 10  # Number of samples to evaluate

device = torch.device('cuda:0')

def log(msg):
    t = time.strftime('%H:%M:%S')
    line = f'[{t}] {msg}'
    print(line, flush=True)
    with open(RESULTS_FILE, 'a') as f:
        f.write(line + '\n')

def load_model_from_checkpoint(ckpt_path=None):
    """Load base model or checkpoint"""
    config = AutoConfig.from_pretrained(MODEL_PATH, trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    config.vocab_size = len(tokenizer)
    config.use_cache = False
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        config=config,
        torch_dtype=torch.bfloat16,
        device_map='auto',
        max_memory={0: '120GiB', 'cpu': '0GiB'},
        trust_remote_code=True,
    )
    
    if ckpt_path and os.path.exists(ckpt_path):
        log(f'Loading checkpoint: {ckpt_path}')
        ckpt = torch.load(ckpt_path, map_location=device)
        model.load_state_dict(ckpt['model_state_dict'])
        log(f'Loaded step {ckpt.get("step", 0)}')
    
    model.eval()
    return model, tokenizer

def evaluate_perplexity(model, tokenizer, sample_files):
    """Evaluate perplexity on sample files"""
    total_loss = 0
    total_tokens = 0
    
    with torch.no_grad():
        for fpath in sample_files:
            data = torch.load(fpath, map_location='cpu', weights_only=False)
            input_ids = data['input_ids'].squeeze(0)[:MAX_SEQ_LEN].unsqueeze(0).to(device)
            
            outputs = model(input_ids=input_ids, labels=input_ids)
            loss = outputs.loss
            
            # Count non-padding tokens
            valid_tokens = (input_ids != tokenizer.pad_token_id).sum().item()
            
            total_loss += loss.item() * valid_tokens
            total_tokens += valid_tokens
    
    avg_loss = total_loss / total_tokens if total_tokens > 0 else float('inf')
    perplexity = math.exp(avg_loss)
    
    return avg_loss, perplexity

# Main evaluation
log('=' * 60)
log('CHECKPOINT EVALUATION')
log('=' * 60)

# Get sample files
sample_files = sorted(glob.glob(os.path.join(HIDDEN_STATES_DIR, '*.pt')))
log(f'Found {len(sample_files)} total samples')
eval_files = sample_files[:EVAL_SAMPLES]
log(f'Evaluating on {len(eval_files)} samples')

# Evaluate base model (no checkpoint)
log('\n--- Base Model (No Training) ---')
model, tokenizer = load_model_from_checkpoint(None)
base_loss, base_ppl = evaluate_perplexity(model, tokenizer, eval_files)
log(f'Loss: {base_loss:.4f} | Perplexity: {base_ppl:.2f}')
del model
torch.cuda.empty_cache()

# Find checkpoints to evaluate
ckpts = []
for prefix in ['standard_step_', 'novel_v2_step_']:
    files = glob.glob(os.path.join(CHECKPOINT_DIR, f'{prefix}*.pt'))
    for f in files:
        try:
            step = int(f.split('step_')[1].split('.')[0])
            ckpts.append((prefix, step, f))
        except:
            pass

# Sort by prefix and step
ckpts.sort(key=lambda x: (x[0], x[1]))

log(f'\nFound {len(ckpts)} checkpoints to evaluate')

# Evaluate each checkpoint
for prefix, step, ckpt_path in ckpts:
    log(f'\n--- {prefix.replace("_", " ").title()} {step} ---')
    try:
        model, tokenizer = load_model_from_checkpoint(ckpt_path)
        loss, ppl = evaluate_perplexity(model, tokenizer, eval_files)
        log(f'Loss: {loss:.4f} | Perplexity: {ppl:.2f}')
        del model
        torch.cuda.empty_cache()
        time.sleep(2)
    except Exception as e:
        log(f'ERROR: {str(e)[:100]}')

log('\n' + '=' * 60)
log('EVALUATION COMPLETE')
log('=' * 60)
