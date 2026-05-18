# LoRA + SAE + Teacher Distillation Training on DGX Spark

## Session: May 7, 2026 — Qwen 27B Expert Logician

### Hardware Context
- DGX Spark (130GB unified memory)
- Qwen3.6-27B base model (~55GB BF16)
- Teacher: FrankenV8-Final (8 layers, Qwen3 config)

### Stable Configuration Found (UPDATED May 7, 2026)

| Parameter | Value | Notes |
|---|---|---|
| LoRA rank | **256** | **VERIFIED sweet spot** — 384 dies during backward pass |
| LoRA alpha | 512 | 2x rank (standard ratio) |
| SAE | Enabled | Feature MSE loss component |
| Teacher distillation | Enabled | MSE on hidden states vs teacher |
| Optimizer | 8-bit AdamW | Memory-efficient |
| Gradient checkpointing | true | Mandatory on unified memory |
| Batch size | 1 | Per-device |
| Gradient accumulation | 4 | Effective batch = 4 (lower = less memory per step) |

### Rank vs Stability Matrix (Empirical)

| Rank | GPU Usage | Margin | Result |
|---|---|---|---|
| 1024 | ~85GB | ~5GB | Dies immediately during backward |
| 768 | ~82GB | ~8GB | Dies on 2nd forward pass |
| 640 | ~80GB | ~10GB | Dies during backward |
| 512 | ~78GB | ~12GB | Dies after multiple backward passes |
| 384 | ~76GB | ~14GB | Dies after ~8 min during backward |
| **256** | **~63GB** | **~27GB** | **STABLE — reached step 110+** |

**Critical insight**: The backward pass allocates gradients for ALL three loss components (CE + distillation + SAE) simultaneously. The ~14GB margin at rank 384 is insufficient for this temporary allocation. Rank 256's ~27GB margin handles it.

### Loss Components (Multi-Objective)

```
Total Loss = w_ce * CE + w_d * D + w_sae * SAE

Where:
- CE = cross-entropy (student's own prediction)
- D = distillation MSE (student vs teacher hidden states)
- SAE = SAE feature MSE (sparse autoencoder reconstruction)
- Weights at step 100: (0.99, 0.20, 0.05) — curriculum weighted
```

### OOM Prevention Checklist

1. **Cache clear before backward**: `torch.cuda.empty_cache()` + `gc.collect()` before `loss.backward()`
2. **Per-layer SAE cleanup**: Delete teacher hidden state tensors after each layer's SAE computation
3. **CPU offload for checkpoints**: Save to CPU first, then disk
4. **Synchronize before saves**: `torch.cuda.synchronize()` to prevent async OOM
5. **Skip optimizer state on resume**: Checkpoint optimizer dict is often incompatible — restart with fresh optimizer
6. **Monitor RSS growth**: If RSS > 25GB, process is leaking — restart
7. **Teacher model on CPU**: Load teacher to CPU (not GPU) — saves ~20GB GPU memory

### Training Log Format

```
Step N/MAX | Loss: X.XXXX (CE:X.XXX D:X.XXX SAE:X.XXX) | W:(w_ce,w_d,w_sae) | LR: X.XXe-XX | GPU: XX.XGB
```

### Checkpoint Resume Pattern

```python
# CRITICAL: Load to CPU first to avoid OOM
if args.resume_from and os.path.exists(args.resume_from):
    checkpoint = torch.load(args.resume_from, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    # Skip optimizer state to save memory
    start_step = checkpoint.get('step', 0)
    del checkpoint
    torch.cuda.empty_cache()
```

### DGX Unresponsiveness Pattern

**Symptom**: SSH times out during training
**Cause**: GPU at 97%+ utilization, system overloaded
**Recovery**: Wait 5-10 minutes OR cycle DGX power
**Prevention**: Don't run monitoring commands during init phase (teacher model loading)

### User Communication Style

- "gimme another status pls" → Short, direct status checks
- "that's too low, bump it to 10k" → Direct commands, no preamble
- "it ready" → DGX cycled and ready for commands
- Values completeness over speed — willing to wait for proper cache generation
- Expects proactive OOM prevention
- HATES redundant tool call loops

### File Locations (Current Run — May 8, 2026)

- Training script: `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py`
- Log file: `/mnt/bigssd/train_r256_final.log`
- Checkpoints: `/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_NNN`
- Master doc: `/data/SpecForge/custom_dflash/MASTER_DOC.md`
- instant_context.py: `/data/SpecForge/custom_dflash/instant_context.py`
- Teacher model: `/data/models/FrankenV8-Final/`
- Post-training scripts: `merge_model.sh`, `evaluate_model.py`, `deploy_hermes_qwen.sh`

## Current Status (May 8, 2026)

- Step: 1770/10000 (17.7%)
- Loss: ~1.975 (down from ~3.0 at step 1560)
- GPU: 62.6GB / 130GB
- Util: 92%
- PID: 443609
- ETA: ~40 hours remaining

## Log Format

```
Step N/MAX | Loss: X.XXXX (CE:X.XXX D:X.XXX SAE:X.XXX) | W:(w_ce,w_d,w_sae) | LR: X.XXe-XX | GPU: XX.XGB
```
