# Continuing Training from Merged Post-Trained Model (May 14, 2026)

## Problem
When a model has already been post-trained (e.g., via FrankenV8 distillation), starting a new training run from the **base uncensored model** discards all prior training work. The correct approach is to continue from the **merged model** (base + prior LoRA weights combined).

## Prior Training State on DGX
```
Base model:     /data/models/Qwen3.6-27B-Uncensored/          (raw, un-tuned)
LoRA adapter:   /data/SpecForge/custom_dflash/checkpoints/final_model/  (r=256, α=512)
Merged model:   /data/SpecForge/custom_dflash/checkpoints/final_model_merged/  (base + LoRA)
```

## How to Distinguish Base vs Merged Model

**Merged model (full weights):**
```bash
$ ls /data/SpecForge/custom_dflash/checkpoints/final_model_merged/
config.json                    # ~3KB
model-00001-of-00002.safetensors   # ~49GB
model-00002-of-00002.safetensors   # ~4GB
model.safetensors.index.json       # ~84KB
# NO adapter_config.json, NO adapter_model.safetensors
```

**LoRA adapter (not merged):**
```bash
$ ls /data/SpecForge/custom_dflash/checkpoints/final_model/
adapter_config.json            # ~1KB
adapter_model.safetensors      # ~5GB
README.md
# Has adapter_config.json with "base_model_name_or_path"
```

## Verification: Check adapter_config.json
```bash
# If adapter_config.json exists, it's a LoRA adapter (not merged)
cat /path/to/model/adapter_config.json
# {
#   "base_model_name_or_path": "/data/models/Qwen3.6-27B-Uncensored/",
#   "peft_type": "LORA",
#   "r": 256,
#   "lora_alpha": 512,
#   ...
# }

# If NO adapter_config.json, it's a merged model (full weights)
ls /path/to/model/adapter_config.json 2>/dev/null || echo "MERGED MODEL (no adapter)"
```

## Training Script Configuration

**WRONG — discards prior training:**
```python
model_path = "/data/models/Qwen3.6-27B-Uncensored/"  # Base model
```

**RIGHT — preserves prior training:**
```python
model_path = "/data/SpecForge/custom_dflash/checkpoints/final_model_merged/"
```

## Verification That Prior Training Is Preserved

Compare Step 0 loss:
| Model Source | Step 0 Loss | Interpretation |
|-------------|-------------|----------------|
| Base uncensored | ~3.40 | No prior training |
| Merged post-trained | ~1.19 | Prior training preserved |

The lower loss from the merged model confirms that the prior training (FrankenV8 distillation) is intact and the new LoRA is building on top of it.

## How LoRA Stacking Works

When you train from a merged model with a new LoRA adapter:
1. The old LoRA weights are now **baked into the base model weights**
2. The new LoRA adapter learns **additional adjustments** on top
3. Both sets of adaptations are preserved — the old ones in the base weights, the new ones in the adapter

This is standard practice for iterative fine-tuning. You can merge again after training to create a new standalone model.

## Common Mistakes

**Mistake 1: "Merged models can't be further tuned"**
- Reality: Merged models are just standard weights files. Load them with `AutoModelForCausalLM.from_pretrained()` and apply a new LoRA adapter.

**Mistake 2: "Start from base to be safe"**
- Reality: Starting from base discards all prior training. The merged model is the correct starting point.

**Mistake 3: Confusing adapter with merged model**
- Check for `adapter_config.json` — if present, it's an adapter (small, ~5GB)
- If absent and there are large `.safetensors` files (~50GB), it's a merged model

## Session Context
- Date: May 14, 2026
- User caught the mistake: "this should be the merged qwen 27b uncensored post-trained model"
- Prior training: LoRA r=256, α=512 on base Qwen 27B (May 8-10, 2026)
- Current training: New LoRA r=256, α=512 on merged post-trained model
- Step 0 loss: 1.1943 (vs 3.4022 from base)
- GPU memory: ~62GB stable
