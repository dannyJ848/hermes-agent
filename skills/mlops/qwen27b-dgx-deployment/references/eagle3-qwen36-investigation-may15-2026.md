# EAGLE-3 Speculative Decoding Investigation — Qwen3.6-27B

**Date:** May 15, 2026
**vLLM Version:** 0.20.2
**Model:** Qwen3.6-27B-Uncensored on DGX Spark (GB10, Blackwell SM121)
**Status:** BLOCKED — Three independent blockers prevent EAGLE-3 from working

## What is EAGLE-3?

EAGLE-3 is a speculative decoding method that trains a small draft head using hidden states from THREE layers of the target model (early, middle, late). In theory it achieves 2-3x speedups with higher acceptance rates than DFlash.

## What Was Tested

### 1. Community Draft Model: Dogacel/specdrift-qwen3.6-27b-eagle3

- **Dimensions match** Qwen3.6-27B: hidden_size=5120, head_dim=256, num_heads=24, num_kv_heads=4, intermediate=17408
- Architecture: `LlamaForCausalLMEagle3` — **supported** by vLLM 0.20.2
- Downloaded to `/data/models/specdrift-qwen3.6-27b-eagle3/`

**Result:** Config validation fails — `hidden_size (5120) is not a multiple of num_attention_heads (24)`
- 5120/24 = 213.33 (not integer)
- True attention dim is 24×256=6144, but Qwen3.6 uses non-standard hidden/head ratio
- vLLM's HF config validator rejects this before model loading

**Attempted workarounds:**
- Modifying config `num_attention_heads` to pass validation: still failed with dimension mismatch
- Installing speculators library in container: succeeded, but doesn't add Qwen3 text-only EAGLE3 support

### 2. Existing Local Draft: /data/models/eagle3-qwen3-draft

- Architecture: `Eagle3Qwen3ForCausalLM` — **NOT supported** by vLLM 0.20.2
- Draft trained for different Qwen3 variant:
  - head_dim: 128 (target Qwen3.6 has 256)
  - num_attention_heads: 32 (target has 24)
  - num_kv_heads: 8 (target has 4)
  - **Weight dimensions incompatible**

**Result:** vLLM 0.20.2 lacks `Eagle3Qwen3ForCausalLM` model class entirely

### 3. Architecture Faking Attempt

Tried modifying the local draft config to use `Eagle3Qwen3vlForCausalLM` (vision-language variant that IS supported):

```bash
cp /data/models/eagle3-qwen3-draft/config.json /data/models/eagle3-qwen3-draft/config.json.bak
python3 -c '
import json
with open("/data/models/eagle3-qwen3-draft/config.json") as f:
    config = json.load(f)
config["architectures"] = ["Eagle3Qwen3vlForCausalLM"]
with open("/data/models/eagle3-qwen3-draft/config.json", "w") as f:
    json.dump(config, f, indent=2)
'
```

**Result:** Model loads but crashes during engine initialization with `KeyError: 'hidden_norm.weight'`
- `Eagle3Qwen3vlForCausalLM` uses `llama_eagle3.py` which expects Llama-style weight names
- Qwen3-style weight names (split projections: `q_proj`, `k_proj`, `v_proj`) mismatch Llama-style (`qkv_proj`)
- Same for MLP: `gate_proj`+`up_proj` vs `gate_up_proj`

## Root Cause Analysis

Qwen3.6-27B uses a **non-standard architecture** where `hidden_size / num_attention_heads` is not integer (5120/24=213.33). This breaks assumptions in:

1. **vLLM's EAGLE-3 support** — Requires matching Qwen3 draft model implementations which don't exist yet
2. **Llama-based EAGLE-3 drafts** — Expect standard attention dimensions where hidden_size is divisible by num_heads
3. **Weight loading** — Llama-style merged projections vs Qwen3-style split projections

## vLLM 0.20.2 Supported EAGLE-3 Architectures

vLLM 0.20.2 natively supports these EAGLE-3 architectures:
- `Eagle3LlamaForCausalLM`
- `LlamaForCausalLMEagle3`
- `Eagle3Qwen3vlForCausalLM` (vision-language only)
- `Eagle3Qwen2_5vlForCausalLM`
- `Eagle3DeepseekV2ForCausalLM`
- `Eagle3DeepseekV3ForCausalLM`

**Missing:** `Eagle3Qwen3ForCausalLM` (text-only Qwen3 models)

## Options to Make EAGLE-3 Work

| Option | Effort | Likelihood |
|--------|--------|------------|
| Train custom EAGLE-3 draft using speculators library | 1-2 weeks | High if done correctly |
| Wait for vLLM update adding `Eagle3Qwen3ForCausalLM` | Unknown | Medium |
| Patch vLLM config validation + weight loading | 3-5 days | Medium |
| Convert draft weights to Llama-compatible format | 1-2 weeks | Low (changes behavior) |

## Current Recommendation

**DFlash remains the only working speculative decoding method for Qwen3.6-27B.**

- DFlash: 16.2 tok/s, 2.45x baseline, lossless quality
- EAGLE-3: Not viable without significant additional work

If EAGLE-3 is critical, the fastest path is training a custom draft using the speculators library with vLLM's hidden state generator on Qwen3.6-27B data.

## Related

- `references/vllm-dflash-deployment-may15-2026.md` — Working DFlash deployment
- `dgx-spark-qwen3-deployment:references/vllm-speedup-landscape-may15-2026.md` — Complete speedup/feature matrix
