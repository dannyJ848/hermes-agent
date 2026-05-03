#!/usr/bin/env python3
"""
Custom hidden state generation for EAGLE-3 using HuggingFace Transformers.
Compatible with SpecForge's train_eagle3.py offline training.

Usage:
    python generate_data_custom.py \
        --model-path /data/models/Qwen3.6-35B-A3B-Uncensored \
        --data-path cache/dataset/ultrachat_train.jsonl/ultrachat_train.jsonl \
        --output-path cache/hidden_states/qwen3.6-35b-a3b-ultrachat \
        --chat-template qwen \
        --max-length 4096 \
        --batch-size 1 \
        --num-samples 10000
"""

import argparse
import json
import os
import re
import torch
from tqdm import tqdm
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, required=True)
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--output-path", type=str, required=True)
    parser.add_argument("--chat-template", type=str, default="qwen")
    parser.add_argument("--max-length", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--num-samples", type=int, default=None)
    parser.add_argument("--trust-remote-code", action="store_true")
    return parser.parse_args()


def load_jsonl(file_path):
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data


def tokenize_conversation(row, tokenizer, max_length):
    messages = row["conversations"]
    formatted = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )
    encoding = tokenizer(
        formatted,
        return_offsets_mapping=True,
        max_length=max_length,
        truncation=True,
    )
    input_ids = encoding.input_ids
    offsets = encoding.offset_mapping
    loss_mask = torch.zeros(len(input_ids), dtype=torch.long)

    # Detect assistant responses for loss mask
    # For Qwen chat template: <|im_start|>assistant\n...<|im_end|>
    assistant_header = "<|im_start|>assistant\n"
    user_header = "<|im_start|>user\n"
    system_header = "<|im_start|>system\n"

    assistant_pattern = (
        re.escape(assistant_header) + r"(.*?)(?=" + re.escape("<|im_start|>") + "|$)"
    )
    for match in re.finditer(assistant_pattern, formatted, re.DOTALL):
        assistant_start_char = match.start(1)
        assistant_end_char = match.end(1)
        for idx, (token_start, token_end) in enumerate(offsets):
            if token_end <= assistant_start_char:
                continue
            if token_start > assistant_end_char:
                continue
            loss_mask[idx] = 1

    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "loss_mask": loss_mask,
        "conversation_str": formatted,
    }


def main():
    args = parse_args()
    os.makedirs(args.output_path, exist_ok=True)

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_path, trust_remote_code=args.trust_remote_code
    )

    # Load model
    print(f"Loading model from {args.model_path}...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        trust_remote_code=args.trust_remote_code,
    )
    model.eval()
    print("Model loaded.")

    # Determine auxiliary layers for EAGLE-3
    num_layers = len(model.model.layers)
    aux_layers = [1, num_layers // 2 - 1, num_layers - 4]
    print(f"Using auxiliary layers: {aux_layers} (total layers: {num_layers})")

    # Load dataset
    print(f"Loading dataset from {args.data_path}...")
    raw_data = load_jsonl(args.data_path)
    if args.num_samples is not None:
        raw_data = raw_data[: args.num_samples]
    print(f"Processing {len(raw_data)} samples...")

    # Process and save
    group_size = 5000
    for idx, row in enumerate(tqdm(raw_data, desc="Generating hidden states")):
        # Group into subdirs for HF upload compatibility
        start = (idx // group_size) * group_size
        end = start + group_size
        grouped_subdir = f"rows_{start}-{end}"
        out_subdir = os.path.join(args.output_path, grouped_subdir)
        os.makedirs(out_subdir, exist_ok=True)

        output_file = os.path.join(out_subdir, f"data_{idx}.ckpt")
        if os.path.exists(output_file):
            continue

        # Tokenize
        tokenized = tokenize_conversation(row, tokenizer, args.max_length)
        input_ids = tokenized["input_ids"].unsqueeze(0).cuda()
        loss_mask = tokenized["loss_mask"].unsqueeze(0)

        with torch.no_grad():
            outputs = model(
                input_ids,
                output_hidden_states=True,
                use_cache=False,
            )
            # Extract auxiliary hidden states (concatenated)
            low = outputs.hidden_states[aux_layers[0]]
            mid = outputs.hidden_states[aux_layers[1]]
            high = outputs.hidden_states[aux_layers[2]]
            aux_hidden_state = torch.cat([low, mid, high], dim=-1).cpu()

            # Last layer hidden state (target)
            hidden_state = outputs.hidden_states[-1].cpu()

        data_point = {
            "input_ids": tokenized["input_ids"],
            "loss_mask": tokenized["loss_mask"],
            "hidden_state": hidden_state.squeeze(0),
            "aux_hidden_state": aux_hidden_state.squeeze(0),
        }
        torch.save(data_point, output_file)

    print(f"Done. Hidden states saved to {args.output_path}")


if __name__ == "__main__":
    main()
