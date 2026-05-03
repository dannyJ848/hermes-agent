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

print('Testing forward pass...')
tokenizer = AutoTokenizer.from_pretrained('/data/models/Qwen3.6-27B-Uncensored', trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

dummy = tokenizer('Hello world', return_tensors='pt').input_ids
# Move to same device as model
if hasattr(model, 'device'):
    dummy = dummy.to(model.device)
else:
    dummy = dummy.cuda()

with torch.no_grad():
    outputs = model(dummy)
print(f'Forward OK! Logits shape: {outputs.logits.shape}')

print('\nTesting backward pass...')
model.train()
outputs = model(dummy, labels=dummy)
loss = outputs.loss
print(f'Loss: {loss.item():.4f}')
loss.backward()
print('Backward OK!')

print('\nGPU memory:')
print(f'  Allocated: {torch.cuda.memory_allocated() / 1e9:.1f}GB')
print(f'  Reserved: {torch.cuda.memory_reserved() / 1e9:.1f}GB')
print(f'  Max: {torch.cuda.max_memory_allocated() / 1e9:.1f}GB')
print('\nALL TESTS PASSED - Custom PyTorch training works!')
