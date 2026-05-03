#!/usr/bin/env python3
"""
Phase 1: Generate hidden states from Qwen3.6-27B target model.
Saves hidden states from target layers [1, 16, 31, 46, 61] to disk.
"""

import argparse
import json
import os
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, required=True)
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--num-samples", type=int, default=None)
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--target-layers", type=int, nargs="+", default=[1, 16, 31, 46, 61])
    return parser.parse_args()

def load_jsonl(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def tokenize_conversation(row, tokenizer, max_length):
    messages = row.get("conversations", row.get("messages", []))
    if not messages:
        # Try alternate formats
        if "input" in row and "output" in row:
            messages = [
                {"role": "user", "content": row["input"]},
                {"role": "assistant", "content": row["output"]}
            ]
        elif "text" in row:
            messages = [{"role": "user", "content": row["text"]}]
    
    formatted = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )
    encoding = tokenizer(
        formatted,
        return_tensors="pt",
        max_length=max_length,
        truncation=True,
        padding=False,
    )
    return encoding["input_ids"][0]

def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Loading tokenizer from {args.model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_path,
        trust_remote_code=args.trust_remote_code,
    )
    
    print(f"Loading target model from {args.model_path}...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        trust_remote_code=args.trust_remote_code,
    )
    model.eval()
    
    num_layers = len(model.model.layers)
    print(f"Model has {num_layers} layers")
    print(f"Extracting hidden states from layers: {args.target_layers}")
    
    # Load dataset
    raw_data = load_jsonl(args.data_path)
    if args.num_samples:
        raw_data = raw_data[:args.num_samples]
    print(f"Processing {len(raw_data)} samples...")
    
    # Process each sample
    for idx, row in enumerate(tqdm(raw_data, desc="Generating hidden states")):
        output_file = os.path.join(args.output_dir, f"sample_{idx:06d}.pt")
        if os.path.exists(output_file):
            continue
        
        input_ids = tokenize_conversation(row, tokenizer, args.max_length)
        input_ids = input_ids.unsqueeze(0).cuda()
        
        with torch.no_grad():
            outputs = model(
                input_ids,
                output_hidden_states=True,
                use_cache=False,
            )
            
            # Extract hidden states from target layers
            hidden_states = []
            for layer_idx in args.target_layers:
                hs = outputs.hidden_states[layer_idx].cpu()  # [1, seq_len, hidden_size]
                hidden_states.append(hs.squeeze(0))
            
            # Stack: [num_target_layers, seq_len, hidden_size]
            stacked = torch.stack(hidden_states, dim=0)
            
            # Also save input_ids for draft training
            input_ids_cpu = input_ids.cpu().squeeze(0)
            
        # Save to disk
        torch.save({
            "input_ids": input_ids_cpu,
            "hidden_states": stacked,  # [5, seq_len, 5120]
            "seq_len": input_ids_cpu.shape[0],
        }, output_file)
        
        # Clear GPU cache periodically
        if idx % 100 == 0:
            torch.cuda.empty_cache()
    
    print(f"Done! Saved {len(raw_data)} samples to {args.output_dir}")
    print(f"Each sample contains hidden states from layers {args.target_layers}")

if __name__ == "__main__":
    main()
