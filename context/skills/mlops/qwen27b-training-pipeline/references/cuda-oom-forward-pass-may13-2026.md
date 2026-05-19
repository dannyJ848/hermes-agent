# CUDA OOM on Forward Pass — Not a Hang

**Date:** May 13, 2026
**System:** DGX Spark GB10 (121GB VRAM)
**Model:** Qwen 27B BF16
**Task:** LoRA fine-tuning with transformers.Trainer

## Symptom

Model loads successfully (~54GB GPU shown in nvidia-smi), but training never starts. Process shows:
- 100% CPU usage
- `futex_do_wait` in kernel stack traces
- No metrics after 5+ minutes
- GPU memory allocated but no GPU utilization

## Initial Misdiagnosis

Thought it was a dataloader deadlock. Tried:
- Rewriting with IterableDataset
- Removing custom WeightedDataset
- Testing DataLoader independently (worked fine)
- Testing Trainer with dummy model (worked fine)

All tests passed. The actual issue only appeared when running the full model.

## Actual Cause

CUDA OOM on first forward pass. The error only surfaces if you:
1. Wait for the crash (takes several minutes of allocator retrying)
2. Or test with `max_steps=3` to see the error quickly

Error signature:
```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 80.00 MiB.
GPU 0 has a total capacity of 121.69 GiB of which 583.20 MiB is free.
This process has 117.79 GiB memory in use.
```

## Memory Breakdown

| Component | Size |
|-----------|------|
| Model weights (BF16) | ~54GB |
| LoRA adapters (r=256) | ~1.3GB |
| Optimizer states (8-bit AdamW) | ~2.6GB |
| Gradients | ~1.3GB |
| Activations (batch=1, seq=4096) | ~2-4GB |
| DataCollator duplication | ~16GB |
| **Total without checkpointing** | **~78GB** |
| Fragmentation overhead | ~40GB |
| **Total with fragmentation** | **~118GB → OOM** |

The futex waits are PyTorch's CUDA memory allocator retrying allocations, not a Python deadlock.

## Fixes Applied

### 1. Gradient Checkpointing
```python
training_args = TrainingArguments(
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
    # ... other args
)
```

### 2. Custom Collator (no tensor duplication)
```python
class CausalLMCollator:
    def __init__(self, pad_token_id=0):
        self.pad_token_id = pad_token_id
    def __call__(self, features):
        return {
            "input_ids": torch.stack([f["input_ids"] for f in features]),
            "attention_mask": torch.stack([f["attention_mask"] for f in features]),
            "labels": torch.stack([f["labels"] for f in features]),
        }
```

### 3. Expandable Segments
```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

### 4. Verification Pattern
Always test with `max_steps=3` before full launch:
```python
args = TrainingArguments(..., max_steps=3, warmup_steps=0)
trainer = Trainer(model=model, args=args, train_dataset=ds, ...)
trainer.train()  # Should complete in <2 min after model load
```

## Key Lesson

"Training never starts" + high CPU + futex waits + GPU memory allocated but no utilization = **OOM during forward pass**, not a dataloader deadlock. Test with tiny step count to confirm.
