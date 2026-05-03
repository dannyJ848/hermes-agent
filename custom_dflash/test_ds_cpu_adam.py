import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

print('Loading Qwen 27B...', flush=True)
model = AutoModelForCausalLM.from_pretrained(
    '/data/models/Qwen3.6-27B-Uncensored',
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
    device_map='auto',
)
model.gradient_checkpointing_enable()
print(f'Params: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B', flush=True)

# Use DeepSpeed CPU Adam - states stay on CPU
print('\nCreating DeepSpeed CPU Adam optimizer...', flush=True)
from deepspeed.ops.adam import DeepSpeedCPUAdam

# DeepSpeedCPUAdam requires params to be on GPU but keeps states on CPU
optimizer = DeepSpeedCPUAdam(model.parameters(), lr=1e-5, betas=(0.9, 0.999), eps=1e-8)
print(f'Optimizer created: {type(optimizer).__name__}', flush=True)

print(f'\nGPU memory before forward:', flush=True)
print(f'  Allocated: {torch.cuda.memory_allocated() / 1e9:.1f}GB', flush=True)
print(f'  Reserved: {torch.cuda.memory_reserved() / 1e9:.1f}GB', flush=True)

print('\nTesting forward + backward + optimizer step...', flush=True)
tokenizer = AutoTokenizer.from_pretrained('/data/models/Qwen3.6-27B-Uncensored', trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
dummy = tokenizer('Hello world', return_tensors='pt').input_ids.to(model.device)

model.train()
print('Forward pass...', flush=True)
outputs = model(dummy, labels=dummy)
loss = outputs.loss
print(f'Loss: {loss.item():.4f}', flush=True)

print('Backward pass...', flush=True)
loss.backward()
print('Backward OK!', flush=True)

print('Optimizer step...', flush=True)
optimizer.step()
optimizer.zero_grad()
print('Optimizer step OK!', flush=True)

print('\nGPU memory after step:', flush=True)
print(f'  Allocated: {torch.cuda.memory_allocated() / 1e9:.1f}GB', flush=True)
print(f'  Reserved: {torch.cuda.memory_reserved() / 1e9:.1f}GB', flush=True)
print(f'  Max: {torch.cuda.max_memory_allocated() / 1e9:.1f}GB', flush=True)

print('\nALL TESTS PASSED - DeepSpeed CPU Adam works!', flush=True)
