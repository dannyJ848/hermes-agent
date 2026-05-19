# Qwen3.5-VL Base + LoRA Merged Model: vLLM Incompatibility and Fallback Patterns

## Problem

When a Qwen3.5-VL base model is fine-tuned with LoRA and the adapter is merged into the base weights, the resulting merged model CANNOT be loaded by vLLM even though it loads fine in transformers.

**Root cause:** The merged model retains visual encoder weights from the VL (vision-language) base, but the chat template / config identifies it as a text-only model. vLLM's Qwen3.5-VL loader expects visual weights to be properly wired, and fails with weight mismatch errors.

## Error Signature

```
torch.nn.modules.module.ModuleAttributeError: 'Qwen2_5_VLForConditionalGeneration' object has no attribute 'visual'
# OR weight shape mismatches in visual.merger.mlp layers
```

## Affected Model

- Base: `Qwen/Qwen3.5-VL` (vision-language variant)
- Training: LoRA fine-tune on text-only data
- Merge: `merged_model/` via PEFT merge_and_unload()
- Result: 51GB BF16 weights that load in transformers but not vLLM

## What Works

### 1. Transformers + FastAPI (Confirmed Working)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "/data/SpecForge/custom_dflash/checkpoints/final_model_merged",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)
```

**Pros:** Loads successfully, generates correct output
**Cons:** ~1-2 tokens/sec on DGX Spark (too slow for interactive use)

### 2. Direct Python Evaluation (Confirmed Working)

For batch tasks (benchmarks, dataset generation), skip the server entirely:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, ...)
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, ...)

# Direct generation — no server overhead
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=512)
```

**Pros:** No server setup, reliable, works with any model that loads in transformers
**Cons:** Still slow (~1-2 tok/s), not suitable for concurrent requests

## What Does NOT Work

### vLLM (Any Version)

```bash
# Fails with visual weight mismatch
vllm serve /data/SpecForge/custom_dflash/checkpoints/final_model_merged \
  --dtype bfloat16 --max-model-len 8192
```

**Attempted fixes that failed:**
- `--max-cudagraph-capture-size 256` — not relevant (different error)
- `--enforce-eager` — not relevant
- Different vLLM versions (0.11.0, 0.11.1) — same error
- `trust_remote_code=True` — no effect (vLLM doesn't pass this through)

### SGLang

Same issue — expects visual weights to be properly configured.

## Workarounds for Interactive Speed

### Option A: Use Text-Only Base Model for Training

If starting a new training run, use `Qwen/Qwen3.5-32B` (text-only) instead of `Qwen/Qwen3.5-VL` as base. The merged model will then load in vLLM without issues.

**Trade-off:** Lose any vision capabilities if you later want them.

### Option B: Strip Visual Weights Post-Merge

After merging, strip the visual encoder weights and re-save:

```python
import torch
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(merged_path, trust_remote_code=True)

# Remove visual encoder
if hasattr(model, 'visual'):
    del model.visual

# Update config
model.config.vision_config = None
model.config.image_token_index = None

# Save
model.save_pretrained(stripped_path)
```

**Untested on this model** — may require additional config adjustments.

### Option C: GGUF Quantization + llama.cpp

Convert merged model to GGUF format and serve via llama.cpp:

```bash
# Convert to GGUF
python convert_hf_to_gguf.py /path/to/merged --outfile model.gguf

# Quantize
./llama-quantize model.gguf model-q4_k_m.gguf Q4_K_M

# Serve
./llama-server -m model-q4_k_m.gguf --host 0.0.0.0 --port 8000
```

**Pros:** 5-10x faster than raw transformers, less VRAM
**Cons:** Quantization quality loss, extra conversion step

### Option D: Accept Slow Inference for Batch Work

For non-interactive use (benchmarks, dataset generation, overnight jobs), the transformers server is fine. Just plan for long runtimes.

## Hermes Agent Integration

When wiring a slow local model into Hermes Agent:

```yaml
# ~/.hermes/config.yaml
model:
  base_url: http://localhost:8000/v1
  api_key: hermes-local
  provider: custom
  default: custom/qwen-27b-expert-logician
```

**Critical:** The model MUST implement `/v1/models` and `/v1/models/{id}` endpoints. Hermes probes these before making chat completion requests. Without them, Hermes will fail silently or timeout.

```python
@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{"id": "qwen-27b-expert-logician", "object": "model", ...}]
    }

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    if model_id == "qwen-27b-expert-logician":
        return {"id": model_id, "object": "model", ...}
    raise HTTPException(status_code=404)
```

## Session-Specific Notes

- **Model path:** `/data/SpecForge/custom_dflash/checkpoints/final_model_merged`
- **Size:** 51GB BF16
- **VRAM usage:** ~26GB at load
- **Generation speed:** ~1-2 tokens/sec (DGX Spark GB10)
- **Verified benchmarks:** MMLU 86.57%, GSM8K 66.19%, HumanEval 82.93%
- **Server script:** `/tmp/qwen_inference_server.py` (FastAPI + transformers)
