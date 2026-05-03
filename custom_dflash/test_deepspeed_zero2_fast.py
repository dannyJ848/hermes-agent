import os
import sys
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['NCCL_P2P_DISABLE'] = '1'
os.environ['NCCL_IB_DISABLE'] = '1'
os.environ['MASTER_ADDR'] = 'localhost'
os.environ['MASTER_PORT'] = '29501'

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import deepspeed

print('='*60)
print('DEEPSPEED ZERO-2 FAST TEST (port 29501)')
print('='*60)

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

print('\n[1/2] Loading Qwen 27B...')
model = AutoModelForCausalLM.from_pretrained(
    '/data/models/Qwen3.6-27B-Uncensored',
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)
model.gradient_checkpointing_enable()
print(f'  Params: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B')

print('\n[2/2] deepspeed.initialize() with 2min timeout...')

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
    
    print('\n[3/3] Forward pass...')
    tokenizer = AutoTokenizer.from_pretrained('/data/models/Qwen3.6-27B-Uncensored', trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    dummy = tokenizer('Hello', return_tensors='pt').input_ids.cuda()
    engine.eval()
    with torch.no_grad():
        out = engine(dummy)
    print(f'  Logits shape: {out.logits.shape}')
    print('\nALL TESTS PASSED')
    
except TimeoutException:
    print('  FAILED: hung for 2 minutes')
    sys.exit(1)
except Exception as e:
    print(f'  FAILED: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
