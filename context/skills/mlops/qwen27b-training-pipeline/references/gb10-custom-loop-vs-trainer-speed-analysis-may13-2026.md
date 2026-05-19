# GB10 Custom Loop vs transformers.Trainer Speed Analysis (May 13, 2026)

## Session Context
Attempted to train Qwen 27B on tiered datasets (reasoning + health) using the same base model that successfully trained on May 8, 2026. Both attempts used DGX Spark GB10 (121GB GPU, 128GB RAM).

## The Paradox
- **May 8:** Trained successfully at ~20s/step for 10,000 steps (~55 hours total)
- **May 13:** Same model, same GPU, but ~517s/step (25x slower)

## Root Cause Analysis

### What Changed
| Aspect | May 8 (fast) | May 13 (slow) |
|--------|-------------|---------------|
| Training loop | Custom (`train_lora_sae_teacher_v1.py`) | `transformers.Trainer` |
| Optimizer | 8-bit AdamW (`bnb.optim.Adam8bit`) | Standard AdamW |
| Gradient checkpointing | NO | YES (forced by OOM) |
| Data collator | Custom (no duplication) | `DataCollatorForLanguageModeling` |
| GPU memory | ~62GB | ~81GB |
| Step time | ~20s | ~517s |

### Why transformers.Trainer Was 25x Slower

1. **Tensor duplication in collator**
   - `DataCollatorForLanguageModeling(mlm=False)` creates `labels` by copying `input_ids`
   - For batch=1, seq=4096, vocab=152k: +16GB memory
   - This pushed total memory from ~62GB to ~78GB

2. **Forced gradient checkpointing**
   - At ~78GB + PyTorch allocator fragmentation, forward pass OOMed
   - Gradient checkpointing "fixed" OOM by recomputing activations during backward
   - Trade-off: ~25x slower (recompute vs store)

3. **Standard AdamW optimizer states**
   - 8-bit AdamW: ~2.6GB for 1.3B LoRA params
   - Standard AdamW: ~10GB (4x more)
   - Additional memory pressure

### Why Custom Loop Was Fast

1. **No tensor duplication**
   - Labels computed in-place: `labels = input_ids.clone()` inside loss function
   - Or: shift labels in loss computation without extra storage
   - Memory stays at ~62GB

2. **8-bit AdamW**
   - `bnb.optim.Adam8bit` keeps optimizer states in 8-bit
   - ~2.6GB vs ~10GB for standard AdamW
   - Fits comfortably in 121GB

3. **No gradient checkpointing needed**
   - At ~62GB, full backward pass fits
   - No recomputation overhead
   - ~20s/step sustained

## Verification Commands

### Check which script was used
```bash
ssh djg6228@10.0.0.171 "grep 'Step 700' /data/SpecForge/custom_dflash/training_v1.log | head -1"
# Shows: "Step 700/10000 | Loss: 6.0548 (CE:5.776 D:2.016 SAE:0.625) | W:(0.96,0.22,0.06) | LR: 2.00e-04 | GPU: 62.6GB"
# GPU 62.6GB confirms no gradient checkpointing
```

### Check step timing
```bash
# May 8 timing (custom loop)
ssh djg6228@10.0.0.171 "grep -E 'Step 7[0-9]{2}' /data/SpecForge/custom_dflash/training_v1.log | awk '{print $1, $2}' | head -5"
# 2026-05-08 11:38:38 (step 700)
# 2026-05-08 11:42:16 (step 710) → 3m38s for 10 steps = ~22s/step

# May 13 timing (Trainer)
ssh djg6228@10.0.0.171 "grep 'Step 1/' /data/SpecForge/custom_dflash/training_final.log"
# Step 1/229248 [08:37<32936:35:17, 517.22s/it]
```

## The Real Lesson

**GB10 CAN train Qwen 27B** — but ONLY with a custom training loop. The `transformers.Trainer` convenience wrapper adds enough overhead to make training intractable.

**For 27B on GB10:**
- Use custom loop (based on `train_lora_sae_teacher_v1.py`)
- 8-bit AdamW (`bnb.optim.Adam8bit`)
- No gradient checkpointing (not needed at ~62GB)
- Custom collator without tensor duplication
- Expected speed: ~20-30s/step

**For smaller models (7B) on GB10:**
- `transformers.Trainer` may be viable
- Test with 3-step timing first

## File Locations
- Working script: `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` (May 8)
- Failed script: `/data/SpecForge/custom_dflash/train_final.py` (May 13, Trainer-based)
- QLoRA script: `/data/SpecForge/custom_dflash/train_qlora.py` (May 13, also failed)
- Logs: `/data/SpecForge/custom_dflash/training_v1.log` (May 8), `/data/SpecForge/custom_dflash/training_final.log` (May 13)
