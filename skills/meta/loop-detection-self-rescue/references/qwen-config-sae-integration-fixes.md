# Qwen3_5Config + SAE Integration Fixes

**Date:** 2026-05-01
**Context:** Integrating Qwen 3.6-27B-Uncensored with Qwen-Scope SAE files for Franken V8 training

## Problem 1: Qwen3_5Config Missing Attributes

**Error:** `AttributeError: 'Qwen3_5Config' object has no attribute 'vocab_size'`
**Then:** `AttributeError: 'Qwen3_5Config' object has no attribute 'hidden_size'`

**Root cause:** Qwen3_5Config uses different attribute names than standard transformers Config.

**Fix pattern — Safe attribute extraction with getattr defaults:**
```python
# Instead of: config.vocab_size
vocab_size = len(tokenizer)  # tokenizer is always loaded first

# Instead of: config.hidden_size
hidden_size = getattr(config, 'hidden_size', getattr(config, 'd_model', 4096))

# Instead of: config.num_attention_heads
num_heads = getattr(config, 'num_attention_heads', getattr(config, 'num_heads', 64))

# Instead of: config.intermediate_size
intermediate_size = getattr(config, 'intermediate_size', getattr(config, 'ffn_dim', 4 * hidden_size))
```

**Key insight:** Load tokenizer BEFORE creating model so `len(tokenizer)` is available.

## Problem 2: SAE Files in float32, Model in bfloat16

**Issue:** SAE weights downloaded from HuggingFace are float32. Loading them as-is wastes GPU memory and causes dtype mismatches.

**Fix:** Cast SAE weights to bfloat16 on load:
```python
def load_sae(sae_path, device='cuda', dtype=torch.bfloat16):
    checkpoint = torch.load(sae_path, map_location=device)
    sae = SimpleSAE(d_model=5120, n_features=81920)
    sae.W_enc.data = checkpoint['W_enc'].to(device).to(dtype)
    sae.b_enc.data = checkpoint['b_enc'].to(device).to(dtype)
    sae.W_dec.data = checkpoint['W_dec'].to(device).to(dtype)
    sae.b_dec.data = checkpoint['b_dec'].to(device).to(dtype)
    sae.to(device).to(dtype).eval()
    for p in sae.parameters():
        p.requires_grad = False
    return sae
```

## Problem 3: Hidden States Path Mismatch

**Error:** `ValueError: num_samples should be a positive integer value, but got num_samples=0`

**Root cause:** Dataset glob pattern `hidden_states_*.pt` didn't match actual files `sample_*.pt`.

**Fix:** Update glob pattern to match actual filenames:
```python
# Was: self.files = sorted(self.hidden_states_dir.glob('hidden_states_*.pt'))
# Fixed: self.files = sorted(self.hidden_states_dir.glob('sample_*.pt'))
```

## Verification Steps

After applying fixes, verify:
1. `python3 -c "from transformers import AutoConfig; c = AutoConfig.from_pretrained('path', trust_remote_code=True); print([a for a in dir(c) if 'size' in a.lower() or 'hidden' in a.lower()])"` — find correct attribute names
2. Check SAE dtype: `torch.load('sae.pt')['W_enc'].dtype` — should be float32, cast to bf16
3. Check hidden states files: `ls hidden_states_dir/` — match glob pattern in code
