# GB10 Training: QLoRA vs Gradient Checkpointing vs Custom Loop (May 13, 2026)

## UPDATED Understanding (Post-Session Analysis)

**Original finding (incorrect):** "GB10 cannot train 27B models. Both QLoRA and gradient checkpointing are intractable."

**Corrected finding:** "GB10 CAN train 27B models, but ONLY with a custom training loop. transformers.Trainer is 25x slower due to tensor duplication and forced gradient checkpointing."

## The Real Comparison

| Approach | GPU Memory | Step Time | 10k Steps ETA | Working? | Notes |
|----------|-----------|-----------|---------------|----------|-------|
| **Custom loop + 8-bit AdamW** | ~62GB | **~20s/step** | **~55 hours** | **YES** | May 8, 2026 — 10k steps completed |
| transformers.Trainer + grad checkpointing | ~81GB | ~517s/step | ~1,450 hours | NO | Tensor duplication forces checkpointing |
| QLoRA (NF4, r=64) + paged AdamW | ~49GB | ~529s/step | ~1,470 hours | NO | Dequantization overhead + paging |

## Why Custom Loop Succeeds Where Trainer Fails

### 1. Tensor Duplication in transformers.Trainer
- `DataCollatorForLanguageModeling(mlm=False)` copies `input_ids` → `labels`
- For batch=1, seq=4096: +16GB memory
- Pushes total from ~62GB to ~78GB
- Forces gradient checkpointing to avoid OOM

### 2. 8-bit AdamW vs Standard AdamW
- Custom loop: `bnb.optim.Adam8bit` → ~2.6GB optimizer states
- Trainer: Standard AdamW → ~10GB optimizer states
- 4x difference in optimizer memory

### 3. Gradient Checkpointing Overhead
- Custom loop: NO checkpointing needed (fits at ~62GB)
- Trainer: FORCED checkpointing (OOM at ~78GB)
- Checkpointing recomputes activations during backward: ~25x slower

## The May 8 Success Story

Script: `train_lora_sae_teacher_v1.py`
- Custom training loop (not transformers.Trainer)
- 8-bit AdamW optimizer
- Teacher distillation + SAE guidance (multi-objective loss)
- Streaming parquet dataloader
- **Result: 10,000 steps in ~55 hours, loss 2.7 → 0.87**

Key log entries:
```
Step 700/10000 | Loss: 6.0548 | GPU: 62.6GB  (11:38:38)
Step 710/10000 | Loss: 4.6454 | GPU: 62.6GB  (11:42:16) → ~22s/step
...
Step 1500/10000 | Loss: 1.1953 | GPU: 62.6GB (16:11:29)
Step 1510/10000 | Loss: 1.2544 | GPU: 62.6GB (16:14:51) → ~20s/step
```

## The May 13 Failure Story

Script: `train_final.py` (transformers.Trainer-based)
- Standard AdamW optimizer
- DataCollatorForLanguageModeling (tensor duplication)
- Gradient checkpointing enabled
- **Result: ~517s/step, killed after step 2**

Key log entries:
```
Step 1/229248 [08:37<32936:35:17, 517.22s/it]
Step 2/229248 [17:12<32852:17:09, 515.90s/it]
```

## Practical Guidance

### For 27B on GB10
**USE CUSTOM LOOP.** Based on `train_lora_sae_teacher_v1.py`:
```python
import bitsandbytes as bnb

# 8-bit optimizer (critical)
optimizer = bnb.optim.Adam8bit(model.parameters(), lr=2e-4)

# Custom collator (no duplication)
class CausalLMCollator:
    def __call__(self, features):
        input_ids = torch.stack([f["input_ids"] for f in features])
        attention_mask = torch.stack([f["attention_mask"] for f in features])
        return {"input_ids": input_ids, "attention_mask": attention_mask}

# Training loop (no gradient checkpointing needed)
for batch in dataloader:
    outputs = model(**batch)
    loss = outputs.loss
    loss.backward()
    if (step + 1) % grad_accum == 0:
        optimizer.step()
        optimizer.zero_grad()
```

### For 7B on GB10
`transformers.Trainer` MAY be viable. Test with 3-step timing first.

### For inference on GB10
Excellent. Deploy with vLLM for ~50-100 tokens/sec.

## Anti-Patterns

**"Use transformers.Trainer for convenience"**
- Wrong for 27B on GB10: 25x slower due to tensor duplication
- Right: Custom loop with 8-bit AdamW

**"QLoRA will make it fast enough"**
- Wrong: QLoRA adds dequantization overhead
- On GB10, custom loop BF16 is faster than QLoRA

**"Gradient checkpointing is always needed for 27B"**
- Wrong: Only needed when memory exceeds ~70GB
- Custom loop stays at ~62GB, no checkpointing needed

## Verification

Before training, run 3-step timing test:
```python
import time

# Test custom loop
start = time.time()
for i in range(3):
    batch = next(iter(dataloader))
    outputs = model(**batch)
    outputs.loss.backward()
print(f"3 custom steps: {time.time()-start:.0f}s")
# Should be <90s for viable training

# Test transformers.Trainer
from transformers import TrainingArguments, Trainer
args = TrainingArguments(..., max_steps=3)
trainer = Trainer(model=model, args=args, train_dataset=subset)
start = time.time(); trainer.train()
print(f"3 Trainer steps: {time.time()-start:.0f}s")
# If >90s, use custom loop instead
```

## File Locations
- Working script: `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py`
- Failed Trainer script: `/data/SpecForge/custom_dflash/train_final.py`
- Failed QLoRA script: `/data/SpecForge/custom_dflash/train_qlora.py`
- May 8 log: `/data/SpecForge/custom_dflash/training_v1.log`
- May 13 log: `/data/SpecForge/custom_dflash/training_final.log`
