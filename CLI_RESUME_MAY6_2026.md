# CLI Resume — Qwen 27B Training (r=1024, Step 130/4000)

**Generated:** May 6, 2026 00:20 UTC
**For:** New Hermes Agent CLI session
**Branch:** `qwen27b-training-artifacts-may3-2026`
**Commit:** `1873cfb3e`

---

## Training Status (LIVE)

| Attribute | Value |
|-----------|-------|
| **Step** | 150/4000 (3.75%) |
| **Loss** | 2.73 (CE:2.44 D:1.43 SAE:0.57) |
| **GPU** | 85.5GB / 130GB |
| **DGX** | 10.0.0.171 (djg6228/6228) |
| **Screen** | `training` (PID 273366, detached, active) |
| **LoRA** | r=1024, alpha=2048 |
| **Trainable** | 5.1B params (15.9% of 32B) |
| **MAX_STEPS** | 4000 (per Kimi recommendation) |
| **Rate** | ~30 sec/step |
| **ETA** | ~32 hours (completion ~May 7, 08:30 UTC) |

**Loss trajectory:**
- Step 4: 6.74 → Step 150: 2.73 = **64% reduction**
- CE: 6.31 → 2.44 (61% drop)
- D: 2.02 → 1.43 (29% drop)
- SAE: 0.65 → 0.57 (stable)

---

## Quick Status Commands

```bash
# Latest 5 steps
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'grep "Step [0-9]*.*Loss" /mnt/bigssd/train_lora_sae_teacher_v1.log | tail -5'

# Process alive check
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'ps -p 273366 -o pid,comm,etime,pcpu,pmem 2>/dev/null || echo "PROCESS_DEAD"'

# Log tail (last 20 lines)
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'tail -20 /mnt/bigssd/train_lora_sae_teacher_v1.log'

# Check for OOM kills
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'dmesg | grep -i "killed process" | tail -3'

# GPU status
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits'
```

---

## File Locations

| File | Path |
|------|------|
| Training log | `/mnt/bigssd/train_lora_sae_teacher_v1.log` |
| Training script | `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` |
| Teacher cache | `/mnt/bigssd/teacher_cache/` (82,014 PKL files) |
| Checkpoints | `/data/SpecForge/custom_dflash/checkpoints/` (empty — first at step 1000) |
| Screen session | `training` (PID 273366) |

---

## If Process Is Dead

1. Check log tail for crash reason: `tail -50 /mnt/bigssd/train_lora_sae_teacher_v1.log`
2. Check for OOM: `dmesg | grep -i 'killed process' | tail -3`
3. Check latest checkpoint: `ls -lt /data/SpecForge/custom_dflash/checkpoints/ | head -5`
4. If checkpoint exists → user decides resume vs restart from 0
5. If no checkpoint → restart from step 0:
   ```bash
   sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'screen -S training -dm bash -c "cd /data/SpecForge/custom_dflash && MAX_STEPS=4000 python3 train_lora_sae_teacher_v1.py > /mnt/bigssd/train_lora_sae_teacher_v1.log 2>&1"'
   ```

---

## Key Config

- **Student:** Qwen3.6-27B-Uncensored (bf16, ~58GB GPU)
- **Teacher:** FrankenV8-Final (8-layer qwen3, CPU for training, cache precomputed)
- **SAEs:** Qwen-Scope at layers [16,32,48] (feature alignment)
- **Loss:** CE (weight 1.0) + hidden-state MSE (weight 0.2) + SAE feature MSE (weight 0.05)
- **Optimizer:** 8-bit AdamW
- **Schedule:** WSD-S (warmup 500, stable 8000, decay 1500) — but MAX_STEPS=4000 truncates
- **Cache keys:** [8,16,32,48] (FrankenV8 layer 8 duplicated to all SAE layers)

---

## Critical Fixes Applied (All Active)

1. **Tokenizer:** Qwen3-0.6B (FrankenV8 has no tokenizer files)
2. **Text format:** `\n\n` double newline (matches precompute)
3. **File order:** `sorted(files)` (matches precompute)
4. **Column handling:** Full multi-format extraction (matches precompute)
5. **Tensor dimension:** `.unsqueeze(0)` for batch dimension
6. **Layer mapping:** Layer 8 duplicated to keys [8,16,32,48]
7. **Gradient checkpointing:** `use_reentrant=False` enabled
8. **batch_size=1:** With grad_accum=4 for effective batch=4

---

## DGX SSH Notes

- **IP:** 10.0.0.171 (IPv4, more reliable than mDNS under load)
- **User:** djg6228 / **Pass:** 6228
- **SSH command:** `sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 '<command>'`
- **Timeouts expected:** Under heavy training load (27B model), SSH may become unresponsive. Do not panic. Wait or check logs instead.
- **Screen session:** Use `screen -r training` to attach, `Ctrl+A D` to detach

---

## Persistence Layers

| Layer | Location |
|-------|----------|
| Memory | "Qwen 27B training LIVE May 6 ~00:15 UTC. LoRA r=1024..." |
| Skill | `mlops/qwen27b-training-pipeline` (SKILL.md + references/) |
| MASTER_DOC | `~/hermes-agent/MASTER_DOC.md` |
| Repo | `dannyJ848/hermes-agent` branch `qwen27b-training-artifacts-may3-2026` commit `1873cfb3e` |

---

## What NOT to Do

- Do NOT run precompute and training simultaneously (OOM kill)
- Do NOT load teacher to GPU during training (OOM kill)
- Do NOT use batch_size > 1 (OOM kill)
- Do NOT use 4-bit quantization (deadlock on Qwen3.6)
- Do NOT attempt full fine-tuning (needs 192GB+ GPU)
- Do NOT trust process_poll session IDs after context compression (use SSH)
- Do NOT loop on identical SSH checks — if output hasn't changed after 3 checks, wait 2-3 minutes

---

## User Preferences

- **Surgical precision:** Kill everything first, then selectively re-enable
- **Action-oriented:** Lead with critical numbers, details after
- **No half-measures:** Wait for full cache, don't start training early
- **Aggressive stability:** Apply ALL fixes simultaneously when instability detected
- **Push from local Mac:** Not DGX SSH under load (use rsync + local git push)

---

*End of resume. Training is LIVE. Check status every 30-60 minutes. Next checkpoint at step 1000.*
