# Qwen3.5 Text-Only + vLLM Incompatibility (May 2026)

**Date:** May 11, 2026
**vLLM version:** 0.20.2
**Model:** Qwen3.5-27B text-only (Qwen3_5ForCausalLM, model_type: "qwen3_5_text")
**Hardware:** NVIDIA DGX Spark (GB10)

## Error

```
TypeError: Invalid type of HuggingFace config. Expected type: Qwen3_5Config,
but found type: Qwen3_5TextConfig
```

## Root Cause

vLLM 0.20.2's Qwen3.5 model handler (`vllm/model_executor/models/qwen3_5.py`) was built for the **multimodal** Qwen3.5-VL model. The text-only variant is a different model class in transformers:

| Variant | transformers Config | model_type | vLLM Handler |
|---------|---------------------|------------|--------------|
| Qwen3.5-VL | `Qwen3_5Config` | `qwen3_5` | ✅ Supported |
| Qwen3.5-Text | `Qwen3_5TextConfig` | `qwen3_5_text` | ❌ Broken |

The error chain:
1. `LLM()` constructor → model loader selects `Qwen3_5ForCausalLM` handler
2. Handler initializes `Qwen3_5ProcessingInfo`
3. `ProcessingInfo.get_hf_config()` demands `Qwen3_5Config` (multimodal)
4. Model has `Qwen3_5TextConfig` → type mismatch

This occurs deep in the model loading path, before any generation happens.

## Workarounds Attempted (All Failed)

### 1. Config swap: Replace config.json with full Qwen3_5Config
Created `Qwen3_5Config` with dummy `vision_config` and saved to model dir.
**Result:** Next error — `Can't load image processor` (no `preprocessor_config.json`)

### 2. Add dummy preprocessor_config.json
Created `preprocessor_config.json` with `Qwen2VLImageProcessor` settings.
**Result:** Process hangs during loading (no further output, likely stuck in vision processor init)

### 3. Monkey-patch multimodal registry to skip processing
Patched `MultiModalRegistry.create_processor` to return `None` for Qwen3.5 models.
**Result:** vLLM still tries to initialize processor, error occurs before registry check.

### 4. Monkey-patch `get_data_parser` / `get_hf_config`
Patched `Qwen3VLMultiModalProcessor.get_data_parser` and `Qwen3_5ProcessingInfo.get_hf_config`.
**Result:** `'dict' object has no attribute 'spatial_merge_size'` or unexpected keyword argument `'tokenizer'`.

### 5. Monkey-patch `create_processor` with tokenizer kwarg handling
Patched to accept `tokenizer` kwarg that vLLM passes.
**Result:** Same `Qwen3_5Config` vs `Qwen3_5TextConfig` type mismatch — the error occurs in `get_hf_config()` before `create_processor` is called.

### 6. Force vLLM 0.19.0 downgrade
Uninstalled 0.20.2, installed 0.19.0.
**Result:** `ImportError: libcudart.so.12` — version mismatch with CUDA 13.0 on GB10.

## Resolution

**Do NOT use vLLM for Qwen3.5 text-only models on vLLM ≤0.20.2.**

Options:
1. **Use direct Python evaluation** with `transformers.AutoModelForCausalLM` — slower but reliable
2. **Wait for vLLM fix** — likely in 0.21.0+ when text-only Qwen3.5 support is added
3. **Use SGLang** — may have same issue if they share config assumptions
4. **Convert to GGUF and use llama.cpp** — works but may affect benchmark accuracy

## Affected Models

Any text-only Qwen3.5 variant:
- Qwen3.5-27B (dense)
- Qwen3.5-14B
- Qwen3.5-7B
- Qwen3.5-1.5B
- Qwen3.5-0.5B

**NOT affected:** Qwen3.5-VL (multimodal) variants — these use `Qwen3_5Config` and work with vLLM.

## Session Reference

- Model path: `/data/SpecForge/custom_dflash/checkpoints/final_model_merged`
- vLLM log: `/tmp/vllm_server.log`
- Direct benchmark script: `/data/SpecForge/custom_dflash/direct_benchmark.py`
- Attempted patches: `/data/SpecForge/custom_dflash/vllm_monkeypatch.py`
