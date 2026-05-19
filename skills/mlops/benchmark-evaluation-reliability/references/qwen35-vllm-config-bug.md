# Qwen3.5 Text-Only Model + vLLM Config Bug (GB10/DGX Spark)

**Date:** May 2026  
**vLLM version:** 0.20.2  
**Model:** Qwen3.5-27B text-only (Qwen3_5ForCausalLM)  
**Error:** `TypeError: Invalid type of HuggingFace config. Expected type: Qwen3_5Config, but found type: Qwen3_5TextConfig`

## Problem

vLLM 0.20.2's Qwen3.5 model handler (`vllm/model_executor/models/qwen3_5.py`) hardcodes multimodal assumptions. When loading a text-only Qwen3.5 model:

1. `Qwen3_5ProcessingInfo.get_hf_config()` calls `ctx.get_hf_config(Qwen3_5Config)`
2. The model's `config.json` has `model_type: "qwen3_5_text"` → transformers returns `Qwen3_5TextConfig`
3. vLLM expects `Qwen3_5Config` (multimodal parent class) → type mismatch

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

## Root Cause

vLLM's Qwen3.5 support was built for the **multimodal** Qwen3.5-VL model. The text-only variant is a different model class in transformers (`Qwen3_5TextConfig` vs `Qwen3_5Config`) but vLLM doesn't have a separate handler for text-only.

The error chain is:
1. `LLM()` constructor → model loader selects `Qwen3_5ForCausalLM` handler
2. Handler initializes `Qwen3_5ProcessingInfo`
3. `ProcessingInfo.get_hf_config()` demands `Qwen3_5Config` (multimodal)
4. Model has `Qwen3_5TextConfig` → type mismatch

This is deep in the model loading path, before any generation happens. Cannot be bypassed without modifying vLLM source code.

## Resolution

**Do NOT use vLLM for Qwen3.5 text-only models on vLLM ≤0.20.2.**

Options:
1. **Use direct Python evaluation** with `transformers.AutoModelForCausalLM` — slower but reliable
2. **Wait for vLLM fix** — likely in 0.21.0+ when text-only Qwen3.5 support is added
3. **Use SGLang** — may have same issue if they share config assumptions
4. **Convert to GGUF and use llama.cpp** — works but may affect benchmark accuracy

## File Paths (Session Reference)

- Model: `/data/SpecForge/custom_dflash/checkpoints/final_model_merged`
- vLLM log: `/tmp/vllm_server.log`
- Direct benchmark script: `/data/SpecForge/custom_dflash/direct_benchmark.py`
