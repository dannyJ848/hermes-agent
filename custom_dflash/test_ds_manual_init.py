import os
import sys
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['NCCL_P2P_DISABLE'] = '1'
os.environ['NCCL_IB_DISABLE'] = '1'
os.environ['MASTER_ADDR'] = 'localhost'
os.environ['MASTER_PORT'] = '29502'
os.environ['RANK'] = '0'
os.environ['LOCAL_RANK'] = '0'
os.environ['WORLD_SIZE'] = '1'

import torch
import torch.distributed as dist
from transformers import AutoModelForCausalLM, AutoTokenizer
import deepspeed

print('='*60)
print('DEEPSPEED MANUAL INIT TEST')
print('='*60)

# Manually init distributed BEFORE deepspeed
print('\n[1/3] Manual distributed init...')
try:
    dist.init_process_group(backend='gloo', rank=0, world_size=1)
    print('  dist.init_process_group() OK')
except Exception as e:
    print(f'  dist.init failed: {e}')
    # Try nccl
    dist.init_process_group(backend='nccl', rank=0, world_size=1)
    print('  dist.init_process_group(nccl) OK')

print('\n[2/3] Loading Qwen 27B...')
model = AutoModelForCausalLM.from_pretrained(
    '/data/models/Qwen3.6-27B-Uncensored',
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)
model.gradient_checkpointing_enable()
print(f'  Params: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B')

print('\n[3/3] deepspeed.initialize() with pre-init distributed...')

ds_config = {
    'bf16': {'enabled': True},
    'zero_optimization': {
        'stage': 2,
        'offload_optimizer': {'device': 'cpu', 'pin_memory': False},
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
        'params': {'lr': 1e-5, 'betas': [0.9, 0.999], 'eps': 1e-8, 'weight_decay': 0.01}
    }
}

import signal
class TimeoutException(Exception): pass
def handler(s, f): raise TimeoutException('init timed out')
signal.signal(signal.SIGALRM, handler)
signal.alarm(120)

try:
    engine, opt, _, _ = deepspeed.initialize(
        model=model,
        model_parameters=model.parameters(),
        config=ds_config
    )
    signal.alarm(0)
    print('  SUCCESS!')
except TimeoutException:
    print('  FAILED: hung for 2 minutes')
    sys.exit(1)
except Exception as e:
    print(f'  FAILED: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
