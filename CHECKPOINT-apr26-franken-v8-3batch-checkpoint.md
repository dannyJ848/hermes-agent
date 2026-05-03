# Franken v8 DFlash Training Checkpoint — Apr 26 2026

## Session Context
- **Date:** Apr 26, 2026 ~17:00 CDT
- **System:** DGX Spark (GB10, 10.0.0.171)
- **Model:** Qwen3.6-27B-Uncensored
- **Objective:** Train Franken v8 draft model with ALL 25 grafts using target_logits

## Current Status

### Problem: Disk Full (100%)
- `/dev/nvme0n1p2` at 100% (3.5TB used / 3.7TB total)
- `hidden_states_with_logits` directory: 2.0TB (4341/9999 samples generated before crash)
- PyTorch broken: `No usable temporary directory found`
- All Python processes failing

### Root Cause
- Target_logits are HUGE: ~600MB per sample (vocab_size=248077 × 4 bytes × seq_len)
- 4341 samples × 600MB = ~2TB, which filled the disk
- Full disk broke temp file creation, which broke PyTorch, which broke everything

## Decision: 3-Batch Approach

Instead of all 9999 samples at once, split into 3 batches of 3333 samples each:
- **Batch 1:** samples 0-3332 (~2TB)
- **Batch 2:** samples 3333-6665 (~2TB)
- **Batch 3:** samples 6666-9998 (~2TB)

Each batch fits in the 3.7TB disk (with cleanup between batches).

## Cleanup Targets (Free ~1.5TB)

| Directory | Size | Action |
|-------------|------|--------|
| `/data/SpecForge/custom_dflash/hidden_states_with_logits` | 2.0TB | **DELETE** |
| `/data/models/Qwen3.6-27B-DFlash-Custom` | 275GB | **DELETE** (old model) |
| `/data/sglang-test-venv` | 9.8GB | **DELETE** (unused) |
| `/data/speculators-venv` | 6.4GB | **DELETE** (unused) |
| `/data/sglang-latest-venv` | 4.5GB | **DELETE** (unused) |
| `/data/models/Qwen3.6-27B-DFlash-vLLM` | 4.2GB | **DELETE** (old model) |
| **Total reclaimable** | **~1.3TB** | |

After cleanup: ~2.2TB free → enough for 1 batch (2TB) + headroom.

## Pipeline Design

### Phase 1: Generate Batch 1 (samples 0-3332)
```bash
# 1. Free disk space
sudo rm -rf /data/SpecForge/custom_dflash/hidden_states_with_logits
sudo rm -rf /data/models/Qwen3.6-27B-DFlash-Custom
sudo rm -rf /data/sglang-test-venv /data/speculators-venv /data/sglang-latest-venv
sudo rm -rf /data/models/Qwen3.6-27B-DFlash-vLLM

# 2. Verify disk space
df -h /

# 3. Generate target_logits for batch 1
cd /data/SpecForge/custom_dflash
python3 regenerate_with_logits.py \
  --input-dir /data/SpecForge/custom_dflash/hidden_states_full \
  --output-dir /data/SpecForge/custom_dflash/batch_1_logits \
  --model-path /data/models/Qwen3.6-27B-Uncensored \
  --max-samples 3333 \
  --bf16
```

### Phase 2: Train Franken v8 on Batch 1
```bash
# Train using batch_1_logits
cd /data/SpecForge/custom_dflash
python3 train_franken_v8_vllm_compatible.py \
  --hidden-states-dir /data/SpecForge/custom_dflash/batch_1_logits \
  --output-dir /data/models/FrankenV8-Batch1 \
  --max-steps 10000 \
  --batch-size 4 \
  --grad-accum 2 \
  --bf16
```

### Phase 3: Cleanup Batch 1, Generate Batch 2
```bash
# Delete batch 1 logits to free space
sudo rm -rf /data/SpecForge/custom_dflash/batch_1_logits

# Generate batch 2
python3 regenerate_with_logits.py \
  --input-dir /data/SpecForge/custom_dflash/hidden_states_full \
  --output-dir /data/SpecForge/custom_dflash/batch_2_logits \
  --model-path /data/models/Qwen3.6-27B-Uncensored \
  --start-idx 3333 \
  --max-samples 3333 \
  --bf16
```

### Phase 4: Train on Batch 2 (resume from Batch 1 checkpoint)
```bash
python3 train_franken_v8_vllm_compatible.py \
  --hidden-states-dir /data/SpecForge/custom_dflash/batch_2_logits \
  --output-dir /data/models/FrankenV8-Batch2 \
  --resume-from /data/models/FrankenV8-Batch1/checkpoint-10000.pt \
  --max-steps 10000 \
  --bf16
```

### Phase 5-6: Repeat for Batch 3

## Key Files
- **Regeneration script:** `/data/SpecForge/custom_dflash/regenerate_with_logits.py`
- **Training script:** `/data/SpecForge/custom_dflash/train_franken_v8_vllm_compatible.py`
- **Original hidden states:** `/data/SpecForge/custom_dflash/hidden_states_full/` (9999 files, 424GB)
- **Target model:** `/data/models/Qwen3.6-27B-Uncensored`

## Franken v8 Grafts Status

With target_logits (this approach): ALL 25 grafts active:
1. Muon Optimizer ✅
2. SwiGLU MLP ✅
3. Manifold Hyper-Connections ✅
4. Gated Attention ✅
5. RoPE ✅
6. MTP-4 ✅
7. Adaptive RMSNorm ✅
8. Highway Connections ✅
9. 8 layers ✅
10. Combined Loss ✅
11. P-EAGLE ✅
12. Dynamic Speculation ✅
13. Bidirectional Context ✅
14. Lookahead Attention ✅
15. PARD ✅
16. Tree Attention ✅
17. Early Exit ✅
18. LK Losses ✅
19. SSD ✅
20. DART ✅
21. LTD ✅
22-25. Additional enhancements ✅

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Disk fills during generation | Monitor with `df -h` every 100 samples |
| Process killed (SSH timeout) | Use `screen` or `tmux` on DGX Spark |
| PyTorch env broken | Fix temp dir first, verify with `python3 -c 'import torch'` |
| Batch takes too long | Each batch: ~4-6 hours generation + 8-10 hours training |
| Checkpoint corruption | Save every 500 steps, verify with `torch.load()` |

## Next Steps (Immediate)

1. **SSH to DGX Spark** and start a `screen` session
2. **Free disk space** (delete targets above)
3. **Fix Python environment** (verify torch works)
4. **Start Batch 1 generation**
5. **Monitor progress** — check disk every 100 samples

## Resume Command

To resume from this checkpoint:
```bash
# On DGX Spark
ssh djg6228@10.0.0.171
screen -S franken_v8

# Then follow Phase 1-6 above
```

---
**Checkpoint saved:** Apr 26, 2026 17:15 CDT
**Label:** `apr26-franken-v8-3batch-checkpoint`
**Status:** Ready to execute — disk cleanup + batch 1 generation
