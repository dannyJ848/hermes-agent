import os
import sys
import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer
import deepspeed

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

print('='*60)
print('MINIMAL DEEPSPEED ZERO-INFINITY TEST v3')
print('='*60)

offload_dir = '/mnt/bigssd/deepspeed_test'
os.makedirs(offload_dir, exist_ok=True)

ds_config = {
    'bf16': {'enabled': True},
    'zero_optimization': {
        'stage': 3,
        'offload_optimizer': {
            'device': 'nvme',
            'nvme_path': offload_dir,
            'pin_memory': False
        },
        'offload_param': {
            'device': 'nvme',
            'nvme_path': offload_dir,
            'pin_memory': False,
            'buffer_size': 2000000000
        },
        'overlap_comm': False,
        'contiguous_gradients': True,
        'sub_group_size': 1e9,
        'reduce_bucket_size': 'auto',
        'stage3_prefetch_bucket_size': 'auto',
        'stage3_param_persistence_threshold': 'auto',
        'stage3_max_live_parameters': 1e9,
        'stage3_max_reuse_distance': 1e9,
        'stage3_gather_16bit_weights_on_model_save': True
    },
    'zero_force_ds_cpu_optimizer': True,
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

print('\n[2/3] Testing deepspeed.initialize()...')
print('  Timeout: 10 minutes')

import signal
class TimeoutException(Exception):
    pass
def timeout_handler(signum, frame):
    raise TimeoutException('deepspeed.initialize() timed out after 10 minutes')

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(600)

try:
    model_engine, optimizer, _, _ = deepspeed.initialize(
        model=model,
        model_parameters=model.parameters(),
        config=ds_config
    )
    signal.alarm(0)
    
    print('  SUCCESS! DeepSpeed engine initialized!')
    
    print('\n[3/3] Testing forward pass...')
    tokenizer = AutoTokenizer.from_pretrained('/data/models/Qwen3.6-27B-Uncensored', trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    dummy_input = tokenizer('Hello world', return_tensors='pt').input_ids.cuda()
    
    model_engine.eval()
    with torch.no_grad():
        outputs = model_engine(dummy_input)
    
    print(f'  Forward pass OK! Logits shape: {outputs.logits.shape}')
    print('\n' + '='*60)
    print('ALL TESTS PASSED - ZeRO-Infinity works!')
    print('='*60)
    
except TimeoutException as e:
    print(f'\n  FAILED: {e}')
    sys.exit(1)
    
except Exception as e:
    print(f'\n  FAILED with error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
