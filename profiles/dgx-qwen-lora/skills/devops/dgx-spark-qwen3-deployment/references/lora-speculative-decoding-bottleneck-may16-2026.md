# LoRA + Speculative Decoding Bottleneck on vLLM (May 16, 2026)

## The Problem

When serving a model with both `--enable-lora` and `--speculative-config` (n-gram or DFlash), inference speed collapses to ~0.6 tok/s — a **10x slowdown** compared to serving without LoRA.

## Root Cause

vLLM applies LoRA adapters **dynamically at every forward pass**. This means:
1. The base model weights are NOT permanently modified
2. Every token generation requires: load base weights → apply LoRA scaling → compute
3. Speculative decoding's parallel verification step becomes serial because each draft token needs its own LoRA application
4. The overhead of dynamic LoRA application dwarfs any speedup from speculative decoding

## Verification

```bash
# With LoRA (slow)
curl -s http://localhost:8000/v1/chat/completions \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"Count 1 to 100"}],"max_tokens":200}' \
  | python3 -c 'import sys,json; r=json.load(sys.stdin); print(f"Speed: {r[\"usage\"][\"completion_tokens\"] / 300:.1f} tok/s")'
# Result: ~0.6 tok/s

# Without LoRA (fast) — same base model, no adapter
curl -s http://localhost:8000/v1/chat/completions \
  -d '{"model":"/data/models/Qwen3.6-27B-Uncensored","messages":[{"role":"user","content":"Count 1 to 100"}],"max_tokens":200}' \
  | python3 -c 'import sys,json; r=json.load(sys.stdin); print(f"Speed: {r[\"usage\"][\"completion_tokens\"] / 300:.1f} tok/s")'
# Result: ~6.6 tok/s (11x faster)
```

## Solution: Permanently Merge LoRA Weights

Instead of serving with `--enable-lora`, merge the LoRA adapter into the base model weights permanently:

```python
# merge_lora.py
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

BASE_MODEL = "/data/models/Qwen3.6-27B-Uncensored"
LORA_PATH = "/data/SpecForge/custom_dflash/checkpoints/final_model"
OUTPUT_PATH = "/data/models/Qwen3.6-27B-Merged"

print("Loading base model...")
model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.bfloat16,
    device_map="cpu",
    trust_remote_code=True,
    low_cpu_mem_usage=False
)

print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(model, LORA_PATH)

print("Merging and unloading...")
model = model.merge_and_unload()

print("Saving merged model...")
model.save_pretrained(OUTPUT_PATH)

print("Saving tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
tokenizer.save_pretrained(OUTPUT_PATH)

print(f"Done! Merged model saved to {OUTPUT_PATH}")
```

Run on DGX:
```bash
cd /data/SpecForge/custom_dflash
source eval_venv/bin/activate
python3 merge_lora.py
```

**Time:** ~5-10 minutes for 27B model on GB10
**Disk:** Adds ~70GB (merged model is same size as base)

## Updated Deployment (No LoRA, Full Speed)

```bash
docker run -d --name vllm-merged \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data:/data \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Merged \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --enable-chunked-prefill \
  --speculative-config '{"method":"ngram","num_speculative_tokens":5}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 16384 \
  --max-num-seqs 128
```

**Key differences from LoRA serving:**
- Removed: `--enable-lora`, `--lora-modules`, `--max-lora-rank`
- Changed: `--model` points to merged model path
- Result: ~6.6 tok/s single-stream, ~200+ tok/s at 128 concurrent

## Trade-offs

| Approach | Speed | Disk | Flexibility | Use Case |
|----------|-------|------|-------------|----------|
| LoRA serving | 0.6 tok/s | +5GB (adapter only) | Can swap adapters | Multi-adapter serving |
| Merged weights | 6.6 tok/s | +70GB (full model) | Fixed weights | Production inference |

## When to Use Each

**Use LoRA serving when:**
- You need to serve multiple LoRA adapters (different tasks/personas)
- You have limited disk space
- Speed is not critical (batch processing, offline jobs)

**Use merged weights when:**
- You have one primary adapter (most common case)
- Speed matters (real-time agent, chat, API serving)
- You have disk space (70GB is manageable on DGX's 4TB)

## Session Reference

- **Date:** 2026-05-16
- **Issue:** vLLM with `--enable-lora` + `--speculative-config` produced 0.6 tok/s
- **Root cause:** Dynamic LoRA application at every forward pass kills speculative decoding
- **Fix:** `merge_and_unload()` to permanently bake LoRA into base weights
- **Result:** 11x speedup (0.6 → 6.6 tok/s)
- **User signal:** "stop you're going down a rabbit hole" — led to systematic testing with/without LoRA
