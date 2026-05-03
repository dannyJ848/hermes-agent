import os
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import deepspeed

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

print('='*60)
print('DEEPSPEED ZERO-2 TEST (optimizer offload to CPU)')
print('='*60)

ds_config = {
    'bf16': {'enabled': True},
    'zero_optimization': {
        'stage': 2,
        'offload_optimizer': {
            'device': 'cpu',
            'pin_memory': False
        },
        'allgather_partitions': True,
        'allgather_bucket_size': 5e8,
        'overlap_comm': False,
        'reduce_scatter': True,
        'reduce_bucket_size': 5e8,
        'contiguous_gradients': True
    },
    'gradient_accumulation_steps': 1,
    'gradient_clipping': 1.0,
    'steps_per_print': 1,
    'train_batch_size': 1,
    'train_micro_batch_size_per_gpu': 1,
    'wall_clock_breakdown': False,
    'optimizer': {
        'type': 'AdamW',
        'params': {
            'lr': 1e-5,
            'betas': [0.9, 0.999],
            'eps': 1e-8,
            'weight_decay': 0.01
        }
    }
}

print('\n[1/3] Loading Qwen 27B to CPU...')
model = AutoModelForCausalLM.from_pretrained(
    '/data/models/Qwen3.6-27B-Uncensored',
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)

print(f'  Model params: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B')

model.gradient_checkpointing_enable()
print('  Gradient checkpointing: ENABLED')

print('\n[2/3] Testing deepspeed.initialize()...')

try:
    model_engine, optimizer, _, _ = deepspeed.initialize(
        model=model,
        model_parameters=model.parameters(),
        config=ds_config
    )
    print('  SUCCESS! DeepSpeed ZeRO-2 engine initialized!')
    
    print('\n[3/3] Testing forward pass...')
    tokenizer = AutoTokenizer.from_pretrained('/data/models/Qwen3.6-27B-Uncensored', trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    dummy_input = tokenizer('Hello world', return_tensors='pt').input_ids.cuda()
    
    model_engine.eval()
    with torch.no_grad():
        outputs = model_engine(dummy_input)
    
    print(f'  Forward pass OK! Logits shape: {outputs.logits.shape}')
    print('\n' + '='*60)
    print('ALL TESTS PASSED - ZeRO-2 works!')
    print('='*60)
    
except Exception as e:
    print(f'\n  FAILED with error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
