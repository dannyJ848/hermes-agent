import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

print('Loading Qwen 27B...')
model = AutoModelForCausalLM.from_pretrained(
    '/data/models/Qwen3.6-27B-Uncensored',
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
    device_map='auto',
)
model.gradient_checkpointing_enable()
print(f'Params: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B')

# Create optimizer - states will be on same device as params (GPU)
# But we can use DeepSpeed's CPU Adam or a custom approach
print('\nCreating AdamW optimizer...')
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
print(f'Optimizer param groups: {len(optimizer.param_groups)}')

# Check where optimizer states are
sample_param = list(model.parameters())[0]
print(f'Sample param device: {sample_param.device}')
print(f'Sample param dtype: {sample_param.dtype}')

print('\nTesting forward + backward + optimizer step...')
tokenizer = AutoTokenizer.from_pretrained('/data/models/Qwen3.6-27B-Uncensored', trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
dummy = tokenizer('Hello world', return_tensors='pt').input_ids.to(model.device)

model.train()
outputs = model(dummy, labels=dummy)
loss = outputs.loss
print(f'Loss: {loss.item():.4f}')

loss.backward()
print('Backward OK!')

print('Optimizer step...')
optimizer.step()
optimizer.zero_grad()
print('Optimizer step OK!')

print('\nGPU memory:')
print(f'  Allocated: {torch.cuda.memory_allocated() / 1e9:.1f}GB')
print(f'  Reserved: {torch.cuda.memory_reserved() / 1e9:.1f}GB')
print(f'  Max: {torch.cuda.max_memory_allocated() / 1e9:.1f}GB')
print('\nALL TESTS PASSED - Full training loop works!')
