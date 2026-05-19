# EAGLE-3 Speculative Decoding Investigation — Qwen3.6-27B

**Date:** May 15, 2026
**vLLM Version:** 0.20.2
**Model:** Qwen3.6-27B-Uncensored on DGX Spark (GB10, Blackwell SM121)
**Investigation Goal:** Evaluate EAGLE-3 as an alternative to DFlash speculative decoding

## Executive Summary

EAGLE-3 speculative decoding is **NOT viable** for Qwen3.6-27B with vLLM 0.20.2. Three independent blockers prevent any working configuration. DFlash remains the only functional speculative decoding method for this model.

## What is EAGLE-3

EAGLE-3 (Efficient Auto-Regressive Language Model Generation with 3-Layer Draft Head) trains a small draft model using hidden states from three layers of the target model (early, middle, late). In theory it achieves 2-3x speedups with higher acceptance rates than DFlash because it uses actual target model hidden states rather than a separate draft model.

## What Was Tested

### Attempt 1: Existing Local Draft (`eagle3-qwen3-draft`)

**Model:** `/data/models/eagle3-qwen3-draft` (previously downloaded)
**Architecture in config:** `Eagle3Qwen3ForCausalLM`
**Result:** vLLM rejects with:
```
ValidationError: Model architectures ['Eagle3Qwen3ForCausalLM'] are not supported for now.
Supported architectures: dict_keys([... Eagle3LlamaForCausalLM, Eagle3Qwen3vlForCausalLM, ...])
```

**Analysis:** vLLM 0.20.2 has `Eagle3Qwen3vlForCausalLM` (vision-language variant) but NOT `Eagle3Qwen3ForCausalLM` (text-only). The draft was trained for a Qwen3 text model but vLLM only supports the VL variant.

### Attempt 2: Faking Architecture as `Eagle3Qwen3vlForCausalLM`

**Approach:** Modified config to use `Eagle3Qwen3vlForCausalLM` architecture
**Result:** Config validation passes, model loading starts, then fails with:
```
KeyError: 'hidden_norm.weight'
```

**Analysis:** `Eagle3Qwen3vlForCausalLM` maps to `llama_eagle3.py` which expects Llama-style weight names:
- `qkv_proj` (merged Q+K+V) vs Qwen3's `q_proj`, `k_proj`, `v_proj` (separate)
- `gate_up_proj` (merged gate+up) vs Qwen3's `gate_proj`, `up_proj` (separate)
- `hidden_norm` not present in Qwen3 drafts

The weight naming mismatch is fundamental — Qwen3.6 uses split projections while Llama uses merged.

### Attempt 3: Community Specdrift Draft (`Dogacel/specdrift-qwen3.6-27b-eagle3`)

**Model:** Downloaded from HuggingFace, dimensions verified to match Qwen3.6-27B
**Architecture in config:** `LlamaForCausalLMEagle3` (supported by vLLM)
**Result:** Config validation fails with:
```
StrictDataclassClassValidationError: hidden_size (5120) is not a multiple of num_attention_heads (24)
```

**Analysis:** Qwen3.6-27B uses non-standard attention dimensions:
- hidden_size: 5120
- num_attention_heads: 24
- head_dim: 256
- But 5120 ≠ 24 × 256 = 6144

This is valid for Qwen3.6 because attention projects TO num_heads×head_dim (6144) and back FROM 6144 to 5120. The hidden_size is the model dimension, not the attention output dimension. vLLM's Llama validator incorrectly assumes hidden_size = num_heads × head_dim.

The specdrift draft weights confirm this architecture:
- `q_proj`: [6144, 10240] → 6144 = 24×256
- `k_proj`: [1024, 10240] → 1024 = 4×256 (num_kv_heads × head_dim)
- `v_proj`: [1024, 10240]
- `o_proj`: [5120, 6144] → 6144 = 24×256

All weight shapes are internally consistent. The validation is wrong.

## Root Cause Analysis

| Blocker | Layer | Details |
|---------|-------|---------|
| Missing architecture | vLLM model registry | `Eagle3Qwen3ForCausalLM` not in `ModelRegistry.get_supported_archs()` |
| Config validation | vLLM config parser | Llama validator assumes `hidden_size = num_heads × head_dim`, fails for Qwen3.6's non-standard dims |
| Weight naming | vLLM weight loader | `Eagle3Qwen3vlForCausalLM` uses Llama-style merged projections, Qwen3 uses split projections |

## What Would Be Needed to Make EAGLE-3 Work

### Option A: Train Custom Draft with Speculators Library

The `speculators` Python package (installed at `/data/speculators` on DGX) can generate EAGLE-3 drafts using vLLM's hidden state generator. This would produce a draft with:
- Correct architecture class (if vLLM adds support)
- OR Llama-compatible weight naming (if trained with Llama architecture)

**Effort:** High — requires training pipeline setup, hidden state extraction, draft training

### Option B: Patch vLLM to Add `Eagle3Qwen3ForCausalLM`

Add a new model class to vLLM that:
1. Registers `Eagle3Qwen3ForCausalLM` in `ModelRegistry`
2. Handles Qwen3-style weight names (split projections)
3. Bypasses or fixes the config validation for non-standard dims

**Effort:** Medium-High — requires vLLM source modification, rebuild, testing

### Option C: Convert Draft Weights to Llama Format

Transform Qwen3-style weights to Llama-style:
- Merge `q_proj`+`k_proj`+`v_proj` → `qkv_proj`
- Merge `gate_proj`+`up_proj` → `gate_up_proj`
- Adjust dimensions to satisfy `hidden_size = num_heads × head_dim`

**Effort:** Medium — but changes model behavior, may degrade draft quality

## Supported EAGLE-3 Architectures in vLLM 0.20.2

```
Eagle2_5_VLForConditionalGeneration
Eagle3DeepseekV2ForCausalLM
Eagle3DeepseekV3ForCausalLM
Eagle3LlamaForCausalLM
Eagle3MiniMaxM2ForCausalLM
Eagle3Qwen2_5vlForCausalLM
Eagle3Qwen3vlForCausalLM       ← Only Qwen3 variant, VL (vision-language) only
EagleDeepSeekMTPModel
EagleLlama4ForCausalLM
EagleLlamaForCausalLM
EagleMiniCPMForCausalLM
EagleMistralLarge3ForCausalLM
LlamaForCausalLMEagle3
```

**Notable absence:** `Eagle3Qwen3ForCausalLM` (text-only Qwen3)

## Conclusion

EAGLE-3 speculative decoding is blocked for Qwen3.6-27B on vLLM 0.20.2. The three blockers (missing architecture, config validation, weight naming) are all fixable but require non-trivial effort. DFlash remains the recommended speculative decoding method with verified 179% speedup.

## References

- DFlash deployment: `qwen27b-dgx-deployment:references/vllm-dflash-deployment-may15-2026.md`
- vLLM speedup landscape: `references/vllm-speedup-landscape-may15-2026.md`
- Speculators library: `/data/speculators` on DGX Spark
