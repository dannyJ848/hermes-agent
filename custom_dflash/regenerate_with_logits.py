#!/usr/bin/env python3
"""
Regenerate hidden states with target_logits for Franken v8 training.
"""

import os
import argparse
from pathlib import Path
from tqdm import tqdm
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=str, default='/data/SpecForge/custom_dflash/hidden_states_full')
    parser.add_argument('--output-dir', type=str, default='/data/SpecForge/custom_dflash/hidden_states_with_logits')
    parser.add_argument('--model-path', type=str, default='/data/models/Qwen3.6-27B-Uncensored')
    parser.add_argument('--max-samples', type=int, default=None)
    parser.add_argument('--bf16', action='store_true', default=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    existing_files = set()
    if args.resume:
        existing_files = {f.name for f in Path(args.output_dir).glob('*.pt')}
        print(f'Resuming: {len(existing_files)} files already processed')
    
    input_files = sorted(Path(args.input_dir).glob('*.pt'))
    if args.max_samples:
        input_files = input_files[:args.max_samples]
    
    if args.resume:
        input_files = [f for f in input_files if f.name not in existing_files]
    
    print(f'Processing {len(input_files)} files...')
    
    print(f'Loading target model from {args.model_path}...')
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Device: {device}')
    
    dtype = torch.bfloat16 if args.bf16 else torch.float32
    
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=dtype,
        device_map='auto',
        trust_remote_code=True,
        attn_implementation='eager',
    )
    model.eval()
    
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    vocab_size = len(tokenizer)
    print(f'Model loaded. Vocab size: {vocab_size}')
    
    for i, input_file in enumerate(tqdm(input_files, desc='Generating logits')):
        try:
            data = torch.load(input_file, map_location='cpu')
            input_ids = data['input_ids']
            hidden_states = data['hidden_states']
            seq_len = data['seq_len']
            
            with torch.no_grad():
                input_ids_batch = input_ids.unsqueeze(0).to(device)
                outputs = model(input_ids_batch, output_hidden_states=False)
                target_logits = outputs.logits[0].cpu()
            
            output_data = {
                'input_ids': input_ids,
                'hidden_states': hidden_states,
                'target_logits': target_logits,
                'seq_len': seq_len,
            }
            
            output_file = Path(args.output_dir) / input_file.name
            torch.save(output_data, output_file)
            
            if (i + 1) % 100 == 0:
                torch.cuda.empty_cache()
                
        except Exception as e:
            print(f'ERROR processing {input_file.name}: {e}')
            continue
    
    print(f'\nDone! Output saved to {args.output_dir}')
    print(f'Total files: {len(list(Path(args.output_dir).glob("*.pt")))}')

if __name__ == '__main__':
    main()
