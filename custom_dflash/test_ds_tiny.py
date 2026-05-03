import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['MASTER_PORT'] = '29503'

import torch
import torch.nn as nn
import deepspeed

print('Testing DeepSpeed with tiny model...')

class TinyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 10)
    def forward(self, x):
        return self.linear(x)

model = TinyModel().cuda()

ds_config = {
    'bf16': {'enabled': False},
    'zero_optimization': {
        'stage': 2,
        'offload_optimizer': {'device': 'cpu', 'pin_memory': False},
    },
    'train_batch_size': 1,
    'train_micro_batch_size_per_gpu': 1,
    'optimizer': {
        'type': 'Adam',
        'params': {'lr': 0.001}
    }
}

print('deepspeed.initialize()...')
engine, opt, _, _ = deepspeed.initialize(
    model=model,
    model_parameters=model.parameters(),
    config=ds_config
)
print('SUCCESS!')

x = torch.randn(1, 10).cuda()
out = engine(x)
print(f'Forward OK: {out.shape}')
