# Direct PEFT Training on DGX Spark GB10 (May 2026)

## Context

After extensive testing, axolotl proved incompatible with GB10 for production training due to config parsing bugs, preprocessing timeouts, and deprecated field handling. This document describes the verified working alternative: direct PEFT + transformers.Trainer.

## Verified Environment

- **Hardware:** DGX Spark GB10 (128GB unified memory, CUDA 13.0)
- **PyTorch:** 2.11.0+cu128 (from NVIDIA wheels)
- **Transformers:** 4.51.3
- **PEFT:** 0.15.4
- **BitsAndBytes:** 0.49.1
- **Model:** Qwen 27B BF16 merged (51GB, /data/SpecForge/custom_dflash/checkpoints/final_model_merged)

## Critical Finding: `low_cpu_mem_usage=False`

When loading models >20B params with `device_map="auto"` for LoRA training, the default `low_cpu_mem_usage=True` causes meta-device offloading. LoRA adapters attach to meta-device parameters, but backward pass fails:

```
RuntimeError: Function MmBackward0 returned an invalid gradient at index 1
- expected device meta but got cuda:0
```

**Always set `low_cpu_mem_usage=False` for training.**

## Verified Training Stack Test

```python
from transformers import AutoModelForCausalLM
from peft import LoraConfig, get_peft_model
import torch

model = AutoModelForCausalLM.from_pretrained(
    '/data/SpecForge/custom_dflash/checkpoints/final_model_merged',
    dtype=torch.bfloat16,
    device_map='cuda:0',
    low_cpu_mem_usage=False  # CRITICAL
)

lora_config = LoraConfig(
    r=256, lora_alpha=512,
    target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],
    lora_dropout=0.05, bias='none'
)
model = get_peft_model(model, lora_config)

# Test forward + backward
x = torch.randint(0, 100000, (1, 512)).cuda()
out = model(x, labels=x)
out.loss.backward()  # Works!

# Test 8-bit AdamW
import bitsandbytes as bnb
optimizer = bnb.optim.AdamW8bit([p for p in model.parameters() if p.requires_grad], lr=2e-4)
optimizer.step()  # Works!
```

## Flash Attention Status

- **flash_attn package:** Cannot build on GB10 (CUDA 13.0 vs PyTorch cu128 mismatch)
- **SDPA (torch native):** Works, enabled by default when `attn_implementation="sdpa"`
- **Flash Attention 2 via kernels library:** `transformers` auto-falls back to `kernels-community/flash-attn2` when `flash_attn` is not installed
- **Performance:** SDPA is sufficient for training; inference serving uses vLLM with FlashInfer

## Training Script Architecture

```python
#!/usr/bin/env python3
import os
import json
import time
from datetime import datetime
from pathlib import Path

import torch
from torch.utils.data import Dataset, ConcatDataset
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, TrainingArguments,
    Trainer, DataCollatorForLanguageModeling, TrainerCallback
)
from peft import LoraConfig, get_peft_model, TaskType

# Paths
MODEL_PATH = '/data/SpecForge/custom_dflash/checkpoints/final_model_merged'
OUTPUT_DIR = '/data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256'
DATASET_DIR = '/data/SpecForge/custom_dflash/datasets'
PREPROCESSED_DIR = '/data/SpecForge/custom_dflash/preprocessed'

# Hyperparameters
LORA_R = 256
LORA_ALPHA = 512
LORA_DROPOUT = 0.05
LEARNING_RATE = 2e-4
NUM_EPOCHS = 2
BATCH_SIZE = 1
GRAD_ACCUMULATION = 4
MAX_SEQ_LENGTH = 4096
WARMUP_STEPS = 100
SAVE_STEPS = 500
LOGGING_STEPS = 10

TARGET_MODULES = ['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']

class TrainingMonitor:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.output_dir / 'training_metrics.jsonl'
        self.start_time = time.time()
        self.step = 0
    
    def log_step(self, loss, lr, epoch=None):
        self.step += 1
        entry = {
            'step': self.step,
            'timestamp': datetime.utcnow().isoformat(),
            'elapsed_seconds': time.time() - self.start_time,
            'loss': loss,
            'learning_rate': lr
        }
        if epoch is not None:
            entry['epoch'] = epoch
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        print(f'Step {self.step}: loss={loss:.4f} lr={lr:.2e}', flush=True)

class ChatDataset(Dataset):
    def __init__(self, file_path, tokenizer, max_length=4096):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = []
        print(f'Loading {file_path}...')
        with open(file_path) as f:
            for line in f:
                data = json.loads(line.strip())
                if 'messages' in data:
                    text = self._messages_to_text(data['messages'])
                elif 'text' in data:
                    text = data['text']
                else:
                    continue
                self.examples.append(text)
        print(f'Loaded {len(self.examples)} examples')
    
    def _messages_to_text(self, messages):
        parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                parts.append(f'<|im_start|>system\n{content}<|im_end|>')
            elif role == 'user':
                parts.append(f'<|im_start|>user\n{content}<|im_end|>')
            elif role == 'assistant':
                parts.append(f'<|im_start|>assistant\n{content}<|im_end|>')
        return '\n'.join(parts)
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        text = self.examples[idx]
        enc = self.tokenizer(text, truncation=True, max_length=self.max_length,
                             padding='max_length', return_tensors='pt')
        return {
            'input_ids': enc['input_ids'].squeeze(),
            'attention_mask': enc['attention_mask'].squeeze(),
            'labels': enc['input_ids'].squeeze()
        }

def setup_model_and_tokenizer():
    print('Loading tokenizer...')
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print('Loading model (~5 min)...')
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map='cuda:0',
        low_cpu_mem_usage=False,  # CRITICAL
        trust_remote_code=True
    )
    print(f'Model loaded. Params: {sum(p.numel() for p in model.parameters())/1e6:.0f}M')
    print(f'GPU memory: {torch.cuda.memory_allocated()/1e9:.1f} GB')
    return model, tokenizer

def apply_lora(model):
    lora_config = LoraConfig(
        r=LORA_R, lora_alpha=LORA_ALPHA,
        target_modules=TARGET_MODULES,
        lora_dropout=LORA_DROPOUT,
        bias='none', task_type=TaskType.CAUSAL_LM
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model

def load_datasets(tokenizer):
    datasets = []
    tier_files = [
        ('tier1-reasoning-chat.jsonl', 'tier1'),
        ('tier2-reasoning-chat.jsonl', 'tier2'),
        ('tier3-health-chat.jsonl', 'tier3'),
    ]
    for filename, name in tier_files:
        filepath = os.path.join(DATASET_DIR, filename)
        if os.path.exists(filepath):
            ds = ChatDataset(filepath, tokenizer, max_length=MAX_SEQ_LENGTH)
            datasets.append(ds)
        else:
            print(f'Warning: {filepath} not found')
    if not datasets:
        raise ValueError('No datasets found!')
    combined = ConcatDataset(datasets)
    print(f'Total examples: {len(combined)}')
    return combined

class MetricsCallback(TrainerCallback):
    def __init__(self, monitor):
        self.monitor = monitor
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs and 'loss' in logs:
            self.monitor.log_step(
                loss=logs.get('loss', 0),
                lr=logs.get('learning_rate', 0),
                epoch=logs.get('epoch')
            )

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    monitor = TrainingMonitor(OUTPUT_DIR)
    model, tokenizer = setup_model_and_tokenizer()
    model = apply_lora(model)
    train_dataset = load_datasets(tokenizer)
    
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        logging_steps=LOGGING_STEPS,
        save_steps=SAVE_STEPS,
        save_total_limit=3,
        bf16=True,
        tf32=True,
        optim='adamw_torch',
        weight_decay=0.0,
        max_grad_norm=1.0,
        dataloader_num_workers=2,
        dataloader_pin_memory=True,
        remove_unused_columns=False,
        report_to=['none'],
        logging_dir=os.path.join(OUTPUT_DIR, 'logs')
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
        callbacks=[MetricsCallback(monitor)]
    )
    
    print('Starting training...')
    trainer.train()
    
    final_path = os.path.join(OUTPUT_DIR, 'final')
    trainer.save_model(final_path)
    print(f'Training complete! Saved to {final_path}')

if __name__ == '__main__':
    main()
```

## Telemetry and Monitoring

### Telemetry Server (HTTP)

```python
# telemetry_server.py
import os, json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

METRICS_FILE = '/data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/training_metrics.jsonl'

def read_latest_metrics(n=50):
    metrics = []
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, 'r') as f:
            lines = f.readlines()
            for line in lines[-n:]:
                try: metrics.append(json.loads(line.strip()))
                except: pass
    return metrics

class TelemetryHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
        elif self.path == '/metrics':
            metrics = read_latest_metrics(100)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(metrics).encode())
        elif self.path == '/status':
            metrics = read_latest_metrics(1)
            if not metrics:
                status = {'status': 'not_started', 'message': 'No metrics found'}
            else:
                latest = metrics[-1]
                last_update = datetime.fromisoformat(latest.get('timestamp', ''))
                now = datetime.utcnow()
                idle_seconds = (now - last_update).total_seconds() if last_update else 0
                status = {
                    'status': 'running' if idle_seconds < 120 else 'stalled',
                    'step': latest.get('step', 0),
                    'loss': latest.get('loss', None),
                    'learning_rate': latest.get('learning_rate', None),
                    'epoch': latest.get('epoch', None),
                    'elapsed_seconds': latest.get('elapsed_seconds', 0),
                    'idle_seconds': idle_seconds,
                    'last_update': latest.get('timestamp'),
                }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    port = int(os.environ.get('TELEMETRY_PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), TelemetryHandler)
    print(f'Telemetry server on http://0.0.0.0:{port}')
    server.serve_forever()
```

### GPU Monitor Daemon

```python
# training_monitor.py
import os, time, subprocess
from datetime import datetime

LOG_FILE = '/tmp/training_monitor.log'

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def check_gpu():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,temperature.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            parts = result.stdout.strip().split(', ')
            return {
                'gpu_util': float(parts[0]),
                'memory_mb': float(parts[1]),
                'temp_c': float(parts[2])
            }
    except:
        pass
    return None

log('Monitor started')
while True:
    time.sleep(30)
    gpu = check_gpu()
    if gpu:
        log(f'GPU: {gpu["gpu_util"]:.1f}% util, {gpu["memory_mb"]:.0f}MB, {gpu["temp_c"]:.1f}C')
    else:
        log('GPU check failed')
```

## Pre-tokenization Strategy

For datasets >1M examples, pre-tokenize to avoid on-the-fly overhead:

```python
# pre_tokenize.py
import os, json
from transformers import AutoTokenizer

MODEL_PATH = '/data/SpecForge/custom_dflash/checkpoints/final_model_merged'
DATASET_DIR = '/data/SpecForge/custom_dflash/datasets'
OUTPUT_DIR = '/data/SpecForge/custom_dflash/preprocessed'
MAX_SEQ_LENGTH = 4096

def messages_to_text(messages):
    parts = []
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'system':
            parts.append(f'<|im_start|>system\n{content}<|im_end|>')
        elif role == 'user':
            parts.append(f'<|im_start|>user\n{content}<|im_end|>')
        elif role == 'assistant':
            parts.append(f'<|im_start|>assistant\n{content}<|im_end|>')
    return '\n'.join(parts)

def pre_tokenize_file(tokenizer, input_file, output_file, max_length=4096):
    print(f'Processing {input_file}...')
    count = 0
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            data = json.loads(line.strip())
            if 'messages' in data:
                text = messages_to_text(data['messages'])
            elif 'text' in data:
                text = data['text']
            else:
                continue
            enc = tokenizer(text, truncation=True, max_length=max_length,
                           padding='max_length', return_tensors='np')
            record = {
                'input_ids': enc['input_ids'][0].tolist(),
                'attention_mask': enc['attention_mask'][0].tolist(),
                'labels': enc['input_ids'][0].tolist()
            }
            f_out.write(json.dumps(record) + '\n')
            count += 1
            if count % 10000 == 0:
                print(f'  Processed {count} examples...')
    print(f'Done! {count} examples written to {output_file}')
    return count

# Run
os.makedirs(OUTPUT_DIR, exist_ok=True)
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

for input_name, output_name in [
    ('tier1-reasoning-chat.jsonl', 'tier1_preprocessed.jsonl'),
    ('tier2-reasoning-chat.jsonl', 'tier2_preprocessed.jsonl'),
    ('tier3-health-chat.jsonl', 'tier3_preprocessed.jsonl'),
]:
    input_path = os.path.join(DATASET_DIR, input_name)
    output_path = os.path.join(OUTPUT_DIR, output_name)
    if os.path.exists(input_path):
        pre_tokenize_file(tokenizer, input_path, output_path, MAX_SEQ_LENGTH)
```

**Rate:** ~15k examples/minute on GB10 CPU (single-threaded)
**Output size:** ~75MB per 1000 examples at 4096 sequence length with padding

## Error Signatures

| Error | Cause | Fix |
|-------|-------|-----|
| `RuntimeError: Function MmBackward0 returned an invalid gradient at index 1 - expected device meta but got cuda:0` | `low_cpu_mem_usage=True` with LoRA | Set `low_cpu_mem_usage=False` |
| `ValueError: size 110Gi is not in a valid format` | Axolotl config `gpu_memory_limit: 110Gi` | Use `110GB` or remove field |
| `FileNotFoundError: whitelist.yaml` | Axolotl telemetry missing file | Create empty `whitelist.yaml` |
| `flash_attn build fails with CUDA version mismatch` | CUDA 13.0 vs PyTorch cu128 | Use SDPA instead; transformers auto-falls back to kernels-community/flash-attn2 |
| `Training process 99% CPU, 0% GPU` | Dataset tokenization bottleneck | Pre-tokenize datasets before training |

## SSH Background Process Pattern

Hermes terminal tool fails with `&`, `nohup`, `setsid` in foreground SSH commands. Use this pattern:

```bash
# Write script on remote host
ssh djg6228@10.0.0.171 "cat > /tmp/start.sh << 'EOF'
#!/bin/bash
cd /data/SpecForge/custom_dflash
~/train-venv/bin/python train_direct.py > /tmp/train.log 2>&1 &
echo $! > /tmp/train.pid
EOF"

# Run script (returns immediately, captures PID)
ssh djg6228@10.0.0.171 "bash /tmp/start.sh; cat /tmp/train.pid"

# Check status
ssh djg6228@10.0.0.171 "ps aux | grep train_direct | grep -v grep"
ssh djg6228@10.0.0.171 "tail -20 /tmp/train.log"
```

## Files

- Training script: `/data/SpecForge/custom_dflash/train_direct.py`
- Telemetry server: `/data/SpecForge/custom_dflash/telemetry_server.py`
- Monitor daemon: `/data/SpecForge/custom_dflash/training_monitor.py`
- Pre-tokenized data: `/data/SpecForge/custom_dflash/preprocessed/`
- Metrics: `/data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/training_metrics.jsonl`
