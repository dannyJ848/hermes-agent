# Meta-Device Gradient Error — May 13, 2026

## Error Signature

```
RuntimeError: Function MmBackward0 returned an invalid gradient at index 1
- expected device meta but got cuda:0
```

## Context

- Model: Qwen 27B BF16 (51GB)
- Hardware: DGX Spark GB10 (128GB unified memory)
- Training: LoRA r=256 with 8-bit AdamW
- Library: transformers + peft + bitsandbytes

## Root Cause

When loading models with `device_map="auto"` and `low_cpu_mem_usage=True` (default), `accelerate` offloads some layers to the "meta" device — a PyTorch fake device that has no actual memory backing. The model appears loaded but most parameters are lazy placeholders.

LoRA's `get_peft_model()` creates adapter weights on whatever device the base parameters are on. When base params are on meta, adapter params are also on meta. During forward pass, PyTorch materializes the needed layers on CUDA. But during backward pass, gradient computation for the LoRA adapters fails because:

1. Base weight is on meta device (no memory)
2. LoRA adapter A/B are on meta device
3. Forward pass computes output on CUDA
4. Backward pass tries to compute dL/dA and dL/dB
5. Gradient tensor is created on CUDA (where computation happened)
6. But the parameter is registered on meta device
7. PyTorch throws: "expected device meta but got cuda:0"

## Reproduction

```python
from transformers import AutoModelForCausalLM
from peft import LoraConfig, get_peft_model
import torch

# BROKEN — low_cpu_mem_usage=True (default)
model = AutoModelForCausalLM.from_pretrained(
    "/data/SpecForge/custom_dflash/checkpoints/final_model_merged",
    torch_dtype=torch.bfloat16,
    device_map="auto",  # or "cuda:0"
    # low_cpu_mem_usage=True is DEFAULT
    trust_remote_code=True
)

lora_config = LoraConfig(r=256, lora_alpha=512, target_modules=["q_proj", "v_proj"])
model = get_peft_model(model, lora_config)

# Forward pass works
out = model(input_ids)

# Backward pass FAILS
out.loss.backward()  # RuntimeError: expected device meta but got cuda:0
```

## Fix

```python
# WORKING — low_cpu_mem_usage=False
model = AutoModelForCausalLM.from_pretrained(
    "/data/SpecForge/custom_dflash/checkpoints/final_model_merged",
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",
    low_cpu_mem_usage=False,  # CRITICAL: prevents meta-device offloading
    trust_remote_code=True
)

lora_config = LoraConfig(r=256, lora_alpha=512, target_modules=["q_proj", "v_proj"])
model = get_peft_model(model, lora_config)

# Forward + backward both work
out = model(input_ids)
out.loss.backward()  # SUCCESS
```

## Verification Steps

1. **Check model device map:**
```python
for name, param in model.named_parameters():
    print(f"{name}: {param.device}")
# BROKEN: shows "meta" for many layers
# WORKING: shows "cuda:0" for all layers
```

2. **Check GPU memory after load:**
```python
import torch
print(f"GPU allocated: {torch.cuda.memory_allocated() / 1e9:.1f} GB")
# BROKEN: ~4GB (most params on meta)
# WORKING: ~54GB (all params on GPU)
```

3. **Test backward pass immediately after model setup:**
```python
dummy_input = torch.randint(0, 32000, (1, 128)).cuda()
out = model(dummy_input, labels=dummy_input)
out.loss.backward()
print("Backward pass OK")
```

## Trade-offs

| Setting | Load Time | GPU Memory | Training Works |
|---------|-----------|------------|----------------|
| `low_cpu_mem_usage=True` | ~30 sec | ~4GB | ❌ Backward fails |
| `low_cpu_mem_usage=False` | ~5 min | ~54GB | ✅ Full training |

On GB10 with 128GB unified memory, the extra memory usage is acceptable.

## When This Applies

- Models >20B parameters
- LoRA/QLoRA training (not inference)
- `device_map="auto"` or `device_map="cuda:0"`
- Any PEFT method that adds trainable parameters

## When NOT Needed

- Model inference only (no backward pass)
- Full fine-tuning (all parameters on GPU anyway)
- Models <7B (usually fit in GPU without meta offloading)
- Using `device_map=None` (loads to CPU, then manual `.to("cuda")`)

## Related

- `references/axolotl-incompatibility-gb10-workaround-may13-2026.md` — Axolotl has same issue but no workaround
- `references/direct-peft-training-may2026.md` — Full direct training script with this fix
