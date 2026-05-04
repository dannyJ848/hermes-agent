#!/usr/bin/env python3
"""EFFICIENT TEST: Load model once, test multiple configurations"""
import os, time, torch, torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

MODEL_PATH = '/data/models/Qwen3.6-27B-Uncensored'
HIDDEN_STATES_DIR = '/data/SpecForge/custom_dflash/hidden_states'
SAE_DIR = '/data/models/Qwen-Scope'
LOG_FILE = '/mnt/bigssd/test_gradient_stability.log'
MAX_STEPS = 15
GRAD_ACCUM = 4
LR = 1e-5
SAE_LAYERS = [16, 32, 48]
device = torch.device('cuda:0')

def log(msg):
    t = time.strftime('%H:%M:%S')
    line = f'[{t}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

sample_file = os.path.join(HIDDEN_STATES_DIR, 'sample_000000.pt')
if not os.path.exists(sample_file):
    sample_file = '/data/SpecForge/custom_dflash/hidden_states_full/sample_000000.pt'

log('Loading model...')
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None: tokenizer.pad_token = tokenizer.eos_token
config = AutoConfig.from_pretrained(MODEL_PATH, trust_remote_code=True)
config.vocab_size = len(tokenizer)
config.use_cache = False
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH, config=config, torch_dtype=torch.bfloat16,
    device_map='auto', max_memory={0: '120GiB', 'cpu': '0GiB'},
    trust_remote_code=True,
)
log('Model loaded')

saes = {}
for layer_idx in SAE_LAYERS:
    sae_path = os.path.join(SAE_DIR, f'layer{layer_idx}.sae.pt')
    if os.path.exists(sae_path):
        sae = torch.load(sae_path, map_location=device)
        saes[layer_idx] = {
            'W_enc': sae['W_enc'].to(device).bfloat16(),
            'b_enc': sae['b_enc'].to(device).bfloat16(),
            'W_dec': sae['W_dec'].to(device).bfloat16(),
            'b_dec': sae['b_dec'].to(device).bfloat16(),
        }

data = torch.load(sample_file, map_location='cpu')
input_ids = data['input_ids'].squeeze(0)[:256].unsqueeze(0).to(device)
labels = input_ids.clone()

def get_feature_acts(residual, sae_dict):
    W_enc = sae_dict['W_enc']; b_enc = sae_dict['b_enc']
    residual = residual.to(W_enc.dtype)
    pre_acts = residual @ W_enc.T + b_enc
    topk_vals, topk_idx = pre_acts.topk(50, dim=-1)
    acts = torch.zeros_like(pre_acts)
    acts.scatter_(-1, topk_idx, topk_vals)
    return acts

def reconstruct_from_features(features, sae_dict):
    W_dec = sae_dict['W_dec']; b_dec = sae_dict['b_dec']
    return features @ W_dec.T + b_dec

def run_test(name, grad_ckpt, sae_hooks, layerwise_lr, max_steps=MAX_STEPS):
    log(''); log('='*60); log(f'TEST: {name}'); log('='*60)
    
    if grad_ckpt:
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
    else:
        model.gradient_checkpointing_disable()
    
    for p in model.parameters():
        p.requires_grad = True
        if p.grad is not None: p.grad = None
    
    hooks = []; captured_features = {}; captured_hidden = {}
    
    if sae_hooks:
        def make_hook(layer_idx):
            def hook(module, input, output):
                hidden = output[0] if isinstance(output, tuple) else output
                if layer_idx in saes and hidden.requires_grad:
                    features = get_feature_acts(hidden, saes[layer_idx])
                    captured_features[layer_idx] = features
                    captured_hidden[layer_idx] = hidden
                return output
            return hook
        for layer_idx in SAE_LAYERS:
            if layer_idx in saes and layer_idx < len(model.model.layers):
                h = model.model.layers[layer_idx].register_forward_hook(make_hook(layer_idx))
                hooks.append(h)
    
    if layerwise_lr:
        embed_params = list(model.model.embed_tokens.parameters())
        other_params = [p for p in model.parameters() if p not in embed_params]
        param_groups = [{'params': embed_params, 'lr': LR*0.1}, {'params': other_params, 'lr': LR}]
        optimizer = torch.optim.SGD(param_groups, lr=LR)
    else:
        optimizer = torch.optim.SGD(model.parameters(), lr=LR)
    
    model.train(); step = 0
    try:
        while step < max_steps:
            captured_features.clear(); captured_hidden.clear()
            outputs = model(input_ids=input_ids, labels=labels)
            loss = outputs.loss
            
            sae_loss = 0.0
            if sae_hooks and saes:
                for layer_idx in SAE_LAYERS:
                    if layer_idx in captured_features and layer_idx in captured_hidden:
                        features = captured_features[layer_idx]
                        original = captured_hidden[layer_idx]
                        reconstructed = reconstruct_from_features(features, saes[layer_idx])
                        sae_loss += F.mse_loss(reconstructed, original).item()
                count = len([l for l in SAE_LAYERS if l in captured_features])
                if count > 0: sae_loss = sae_loss / count
            
            combined = loss + 0.05 * torch.tensor(sae_loss, device=device, dtype=torch.bfloat16)
            scaled = combined / GRAD_ACCUM
            scaled.backward()
            
            if (step + 1) % GRAD_ACCUM == 0:
                grad_norm = 0.0
                for p in model.parameters():
                    if p.grad is not None: grad_norm += p.grad.norm(2).item() ** 2
                grad_norm = grad_norm ** 0.5
                
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step(); optimizer.zero_grad()
                
                gpu_mem = torch.cuda.memory_allocated(device) / 1e9
                log(f'  Step {step+1}: Loss={loss.item():.4f} | SAELoss={sae_loss:.4f} | GradNorm={grad_norm:.2f} | GPU={gpu_mem:.1f}GB')
                
                if grad_norm > 1000 or torch.isnan(loss) or torch.isinf(loss):
                    log(f'  EXPLOSION! GradNorm={grad_norm:.2f}'); break
            
            step += 1
        log(f'  COMPLETED {step} steps')
    except Exception as e:
        log(f'  ERROR: {type(e).__name__}: {str(e)[:100]}')
    finally:
        for h in hooks: h.remove()
        del optimizer; torch.cuda.empty_cache()

log(''); log('='*60); log('GRADIENT STABILITY TEST SUITE'); log('='*60)

tests = [
    ('Baseline: SGD only', False, False, False),
    ('SGD + grad checkpointing', True, False, False),
    ('SGD + SAE hooks', False, True, False),
    ('SGD + SAE + grad ckpt', True, True, False),
    ('SGD + SAE + grad ckpt + layerwise LR', True, True, True),
]

for name, grad_ckpt, sae_hooks, layerwise_lr in tests:
    run_test(name, grad_ckpt, sae_hooks, layerwise_lr)
    time.sleep(2)

log(''); log('='*60); log('ALL TESTS COMPLETE'); log('='*60)
