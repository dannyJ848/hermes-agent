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

# Memory-efficient CPU-offloaded AdamW with lazy initialization
class LazyCPUAdamW(torch.optim.Optimizer):
    def __init__(self, params, lr=1e-5, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0):
        defaults = dict(lr=lr, betas=betas, eps=eps, weight_decay=weight_decay)
        super().__init__(params, defaults)
        self.initialized = False
    
    def _lazy_init(self):
        if self.initialized:
            return
        print('Lazy initializing optimizer states on CPU...', flush=True)
        total_elements = 0
        for group in self.param_groups:
            for p in group['params']:
                state = self.state[p]
                # Create states on CPU in fp32
                state['exp_avg'] = torch.zeros(p.shape, device='cpu', dtype=torch.float32)
                state['exp_avg_sq'] = torch.zeros(p.shape, device='cpu', dtype=torch.float32)
                state['step'] = 0
                total_elements += p.numel() * 2
        print(f'Optimizer states: {total_elements * 4 / 1e9:.1f}GB on CPU', flush=True)
        self.initialized = True
    
    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        
        if not self.initialized:
            self._lazy_init()
        
        for group in self.param_groups:
            beta1, beta2 = group['betas']
            lr = group['lr']
            eps = group['eps']
            weight_decay = group['weight_decay']
            
            for p in group['params']:
                if p.grad is None:
                    continue
                
                grad = p.grad
                if weight_decay != 0:
                    grad = grad + weight_decay * p
                
                state = self.state[p]
                exp_avg = state['exp_avg'].to(p.device, non_blocking=True)
                exp_avg_sq = state['exp_avg_sq'].to(p.device, non_blocking=True)
                step = state['step'] + 1
                
                exp_avg.mul_(beta1).add_(grad, alpha=1 - beta1)
                exp_avg_sq.mul_(beta2).addcmul_(grad, grad, value=1 - beta2)
                
                bias_correction1 = 1 - beta1 ** step
                bias_correction2 = 1 - beta2 ** step
                step_size = lr / bias_correction1
                denom = (exp_avg_sq.sqrt() / (bias_correction2 ** 0.5)).add_(eps)
                
                p.addcdiv_(exp_avg, denom, value=-step_size)
                
                # Move states back to CPU
                state['exp_avg'].copy_(exp_avg.cpu(), non_blocking=True)
                state['exp_avg_sq'].copy_(exp_avg_sq.cpu(), non_blocking=True)
                state['step'] = step
                
                # Free GPU copies
                del exp_avg, exp_avg_sq
        
        return loss

print('\nCreating Lazy CPU-offloaded AdamW optimizer...', flush=True)
optimizer = LazyCPUAdamW(model.parameters(), lr=1e-5)
print('Optimizer created (states not yet allocated)', flush=True)

print(f'\nGPU memory before forward:', flush=True)
print(f'  Allocated: {torch.cuda.memory_allocated() / 1e9:.1f}GB', flush=True)

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

print('Optimizer step (will lazy-init states)...', flush=True)
optimizer.step()
optimizer.zero_grad()
print('Optimizer step OK!', flush=True)

print('\nGPU memory after step:', flush=True)
print(f'  Allocated: {torch.cuda.memory_allocated() / 1e9:.1f}GB', flush=True)
print(f'  Reserved: {torch.cuda.memory_reserved() / 1e9:.1f}GB', flush=True)
print(f'  Max: {torch.cuda.max_memory_allocated() / 1e9:.1f}GB', flush=True)

# Check CPU memory
import psutil
cpu_used = psutil.Process().memory_info().rss / 1e9
print(f'\nProcess CPU memory: {cpu_used:.1f}GB', flush=True)

print('\nALL TESTS PASSED - Lazy CPU AdamW works!', flush=True)
