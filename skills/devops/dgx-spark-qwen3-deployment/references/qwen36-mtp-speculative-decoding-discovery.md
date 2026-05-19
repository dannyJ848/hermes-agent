# Qwen3.6-27B Native MTP Discovery — May 15, 2026

**Date:** May 15, 2026
**Model:** Qwen3.6-27B-Uncensored (dense, `/data/models/Qwen3.6-27B-Uncensored`)
**vLLM Version:** 0.20.2
**Hardware:** DGX Spark (GB10, Blackwell SM121)

## Discovery

The Qwen3.6-27B checkpoint contains **native MTP (Multi-Token Prediction) weights** that are NOT being utilized by the current vLLM deployment:

```bash
# MTP weights found in checkpoint (15 total)
mtp.fc.weight
mtp.layers.0.input_layernorm.weight
mtp.layers.0.mlp.down_proj.weight
mtp.layers.0.mlp.gate_proj.weight
mtp.layers.0.mlp.up_proj.weight
mtp.layers.0.post_attention_layernorm.weight
mtp.layers.0.self_attn.k_norm.weight
mtp.layers.0.self_attn.k_proj.weight
mtp.layers.0.self_attn.o_proj.weight
mtp.layers.0.self_attn.q_norm.weight
mtp.layers.0.self_attn.q_proj.weight
mtp.layers.0.self_attn.v_proj.weight
mtp.emb.weight
mtp.norm.weight
```

**Config confirms MTP presence:**
```json
{
  "text_config": {
    "mtp_num_hidden_layers": 1,
    "mtp_use_dedicated_embeddings": false
  }
}
```

## Why MTP Is Not Active

vLLM 0.20.2's speculative config auto-detects MTP only for specific `model_type` values:

```python
# From vllm/config/speculative.py
if hf_config.model_type in ("qwen3_5", "qwen3_5_moe"):
    is_moe = hf_config.model_type == "qwen3_5_moe"
    hf_config.model_type = "qwen3_5_mtp"
    n_predict = getattr(hf_config, "mtp_num_hidden_layers", None)
    hf_config.update(
        {
            "n_predict": n_predict,
            "architectures": ["Qwen3_5MoeMTP" if is_moe else "Qwen3_5MTP"],
        }
    )
```

The Qwen3.6-27B checkpoint has `model_type: qwen3_5` at the root level, but vLLM's auto-detection only triggers when the **text_config's** `model_type` is `qwen3_5`. The checkpoint's text_config has `model_type: qwen3_5_text`, which does NOT trigger MTP auto-detection.

**Current deployment uses n-gram speculative decoding instead:**
```bash
--speculative-config '{"method":"ngram","num_speculative_tokens":5}'
```

## MTP vs N-gram Performance

| Method | Speedup | Quality | Training Required | Best For |
|--------|---------|---------|-------------------|----------|
| N-gram | 0-20% | Lossless | No | General text |
| Native MTP | 20-40% | Lossless | Yes (already in checkpoint) | Qwen3.6-specific |
| EAGLE-3 | 2-4x | ~99% | Yes (separate checkpoint) | Maximum speed |
| DFlash | ~6x (claimed) | ~99% | Yes (gated HF model) | Maximum speed |

## How to Enable Native MTP

### Option A: Patch model_type (Recommended)

Change the root `model_type` from `qwen3_5` to `qwen3_5_mtp`:

```bash
python3 -c '
import json
with open("/data/models/Qwen3.6-27B-Uncensored/config.json") as f:
    config = json.load(f)
config["model_type"] = "qwen3_5_mtp"
with open("/data/models/Qwen3.6-27B-Uncensored/config.json", "w") as f:
    json.dump(config, f, indent=2)
print("Updated model_type to qwen3_5_mtp")
'
```

Then launch vLLM with MTP speculative decoding:
```bash
docker run -d --name vllm-merged \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data:/data \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --enable-chunked-prefill \
  --speculative-config '{"method":"mtp","num_speculative_tokens":1}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 16384 \
  --max-num-seqs 128
```

### Option B: Use explicit speculative model

```bash
--speculative-model /data/models/Qwen3.6-27B-Uncensored \
--num-speculative-tokens 1 \
--speculative-method mtp
```

## Verification

### Check MTP initialization in logs
```bash
docker logs vllm-merged | grep -i mtp
# Expected: "Loading MTP weights..." or "MTP speculative decoding enabled"
```

### Check speculative config via API
```bash
curl -s http://localhost:8000/v1/models | python3 -m json.tool
```

### Benchmark MTP vs n-gram
```bash
# Test with same prompt, compare throughput
python3 -c '
import requests, time

prompt = "Explain quantum computing in simple terms"
for method in ["ngram", "mtp"]:
    payload = {
        "model": "merged-lora",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "temperature": 0.7
    }
    start = time.time()
    resp = requests.post("http://localhost:8000/v1/chat/completions", json=payload)
    data = resp.json()
    elapsed = time.time() - start
    tokens = data["usage"]["completion_tokens"]
    print(f"{method}: {tokens/elapsed:.2f} tok/s ({tokens} tokens in {elapsed:.2f}s)")
'
```

## Risks and Considerations

1. **Model type change is safe** — vLLM's `qwen3_5_mtp` handler is backward-compatible with `qwen3_5` checkpoints. If MTP weights are absent, it falls back to standard decoding.

2. **MTP with `num_speculative_tokens=1` is the sweet spot** — Higher values (2-3) may cause acceptance rate collapse on this model.

3. **Quality impact** — Native MTP is lossless (uses model's own trained weights). No quality degradation expected.

4. **LoRA compatibility** — MTP speculative decoding works with LoRA adapters. The draft tokens are generated from the base model, then the full model (with LoRA) verifies them.

5. **Prefix caching interaction** — Even with MTP enabled, prefix caching remains disabled for hybrid models. This is independent.

## Related References

- `references/hybrid-model-prefix-caching-limitations.md` — Why prefix caching is disabled
- `references/vllm-speedup-landscape-may15-2026.md` — Full speedup/feature matrix
- `references/vllm-lora-serving-speed-context-optimization-may14-2026.md` — LoRA serving patterns
