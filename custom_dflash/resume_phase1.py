#!/usr/bin/env python3
"""Resume hidden state generation from existing progress."""
import os
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM

# Config
MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored"
DATA_PATH = "/data/SpecForge/cache/dataset/ultrachat_train.jsonl/ultrachat_train.jsonl"
OUTPUT_DIR = "/data/SpecForge/custom_dflash/hidden_states_full"
MAX_LENGTH = 1024
TRUST_REMOTE_CODE = True
TARGET_LAYERS = [1, 16, 31, 46, 61]

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Check existing files
existing = set()
for f in os.listdir(OUTPUT_DIR):
    if f.endswith('.pt') and f.startswith('sample_'):
        try:
            num = int(f.split('_')[1].split('.')[0])
            existing.add(num)
        except:
            pass

print(f"Found {len(existing)} existing samples")

# Load model
print(f"Loading model from {MODEL_PATH}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=TRUST_REMOTE_CODE)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
    trust_remote_code=TRUST_REMOTE_CODE,
)
model.eval()
print(f"Model loaded. {len(model.model.layers)} layers")

# Load dataset
import json
raw_data = []
with open(DATA_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            raw_data.append(json.loads(line))

print(f"Dataset: {len(raw_data)} samples total")

# Generate missing samples
for idx, row in enumerate(tqdm(raw_data, desc="Generating hidden states")):
    if idx in existing:
        continue
    
    output_file = os.path.join(OUTPUT_DIR, f"sample_{idx:06d}.pt")
    
    # Tokenize
    messages = row.get("conversations", row.get("messages", []))
    if not messages:
        if "input" in row and "output" in row:
            messages = [
                {"role": "user", "content": row["input"]},
                {"role": "assistant", "content": row["output"]}
            ]
        elif "text" in row:
            messages = [{"role": "user", "content": row["text"]}]
    
    formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    encoding = tokenizer(formatted, return_tensors="pt", max_length=MAX_LENGTH, truncation=True, padding=False)
    input_ids = encoding["input_ids"][0].unsqueeze(0).cuda()
    
    with torch.no_grad():
        outputs = model(input_ids, output_hidden_states=True, use_cache=False)
        hidden_states = []
        for layer_idx in TARGET_LAYERS:
            hs = outputs.hidden_states[layer_idx].cpu().squeeze(0)
            hidden_states.append(hs)
        stacked = torch.stack(hidden_states, dim=0)
        input_ids_cpu = input_ids.cpu().squeeze(0)
    
    torch.save({
        "input_ids": input_ids_cpu,
        "hidden_states": stacked,
        "seq_len": input_ids_cpu.shape[0],
    }, output_file)
    
    if idx % 100 == 0:
        torch.cuda.empty_cache()

print(f"Done! Total samples: {len(os.listdir(OUTPUT_DIR))}")
