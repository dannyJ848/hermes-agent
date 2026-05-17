# Merged LoRA Model Produces Garbled Output on Qwen3.5/3.6

Date: May 16, 2026
Model: Qwen3.6-27B-Uncensored + custom_dflash LoRA adapter
Method: peft.merge_and_unload()
vLLM: 0.20.2

## Symptom

After running `peft.merge_and_unload()`, the merged model produces garbled/token salad output:

```
Here's a thinking process:

1.  **Analyze User Input:**
   - User says: "Hello, how are you?"
   - This is a standard greeting and a polite inquiry about my status.

2.  **Identify Key Components:**
```

The output is structurally coherent (follows thinking process format) but semantically broken — it describes analyzing the user's input rather than responding to it.

## Root Cause

`peft.merge_and_unload()` doesn't properly handle Qwen3.5's non-standard attention architecture:

- `hidden_size=5120`
- `num_heads=24`
- `head_dim=256`
- **But 5120 ≠ 24×256 = 6144**

The attention dimensions don't follow the standard `hidden_size = num_heads × head_dim` relationship. The merge operation likely corrupts the weight matrices by assuming standard dimensions.

## Affected Configurations

Both merge approaches fail:

1. **Text-only merge** (AutoModelForCausalLM + merge_and_unload)
2. **Vision-preserving merge** (AutoModelForCausalLM + merge_and_unload + copy preprocessor_config.json)

The vision-preserving merge produces the same garbled output, confirming the issue is in the text layer weight merge, not vision components.

## Verification

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base
base = AutoModelForCausalLM.from_pretrained("/data/models/Qwen3.6-27B-Uncensored")

# Load LoRA
model = PeftModel.from_pretrained(base, "/data/SpecForge/custom_dflash/checkpoints/final_model")

# Merge
merged = model.merge_and_unload()
merged.save_pretrained("/data/SpecForge/custom_dflash/checkpoints/final_model_merged/")

# Test — produces garbled output
tokenizer = AutoTokenizer.from_pretrained("/data/models/Qwen3.6-27B-Uncensored")
inputs = tokenizer("Hello", return_tensors="pt")
outputs = merged.generate(**inputs, max_new_tokens=50)
print(tokenizer.decode(outputs[0]))
# → "Here's a thinking process:\n\n1.  **Analyze User Input:**..."
```

## Workaround

**Use base model + dynamic LoRA instead of merged model.**

vLLM supports dynamic LoRA loading with `--enable-lora` and `--lora-modules`. The base model serves normally, and LoRA weights are applied per-request. This is the only working configuration that preserves both:
- Dynamic LoRA switching
- Vision capabilities
- Speculative decoding (with caveats, see pitfall #38)

## Deployment Command (Working)

```bash
docker run -d \
  --name vllm-base-lora \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/SpecForge/custom_dflash/checkpoints \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --max-lora-rank 256 \
  --lora-modules custom-model=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --speculative-config '{"method": "dflash", "model": "/data/models/Qwen3.5-27B-DFlash", "num_speculative_tokens": 8}' \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.95 \
  --dtype bfloat16
```

## Related

- `references/base-lora-dflash-performance-may16-2026.md` — Performance results for base+LoRA+DFlash
- `references/vision-preserving-lora-merge-may16-2026.md` — Attempted vision-preserving merge (also fails)
- Pitfall #38 in SKILL.md — Base+LoRA+DFlash viable configuration
