import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['LOCAL_RANK'] = '0'
os.environ['RANK'] = '0'
os.environ['WORLD_SIZE'] = '1'
os.environ['MASTER_ADDR'] = 'localhost'
os.environ['MASTER_PORT'] = '29507'

import sys
import torch
from transformers import AutoModelForCausalLM
import deepspeed

print('Loading Qwen 27B...', flush=True)
model = AutoModelForCausalLM.from_pretrained(
    '/data/models/Qwen3.6-27B-Uncensored',
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)
model.gradient_checkpointing_enable()
print(f'Params: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B', flush=True)

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
    'train_batch_size': 1,
    'train_micro_batch_size_per_gpu': 1,
    'optimizer': {
        'type': 'AdamW',
        'params': {'lr': 1e-5, 'betas': [0.9, 0.999], 'eps': 1e-8, 'weight_decay': 0.01}
    }
}

print('deepspeed.initialize()...', flush=True)
try:
    engine, opt, _, _ = deepspeed.initialize(
        model=model,
        model_parameters=model.parameters(),
        config=ds_config
    )
    print('SUCCESS!', flush=True)
except Exception as e:
    print(f'FAILED: {type(e).__name__}: {e}', flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
