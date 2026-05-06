# CLI Resume — Qwen 27B Training (r=1024, Restarted Step 0/4000)

**Generated:** May 6, 2026 11:55 UTC
**For:** New Hermes Agent CLI session
**Branch:** `qwen27b-training-artifacts-may3-2026`
**Commit:** `6621c1613` (with upstream cherry-picks)

---

## Training Status (RESTARTED — Step 0)

| Attribute | Value |
|-----------|-------|
| **Step** | 0/4000 (0%) |
| **Previous** | 490/4000 lost (OOM at checkpoint save) |
| **Loss** | N/A (just started) |
| **GPU** | TBD / 130GB |
| **DGX** | 10.0.0.171 (djg6228/6228) |
| **PID** | 590094 (new restart) |
| **Screen** | None (running via nohup) |
| **LoRA** | r=1024, alpha=2048 |
| **Trainable** | 5.1B params (15.9% of 32B) |
| **MAX_STEPS** | 4000 |
| **save_every** | 1000 (was 500, changed to reduce OOM) |
| **Checkpoint fix** | CPU offload + empty_cache + synchronize before save |
| **Rate** | ~30 sec/step |
| **ETA** | ~33 hours (completion ~May 7, 21:00 UTC) |

**Loss trajectory (previous run, for reference):**
- Step 4: 6.74 → Step 490: 1.6-2.5 (65%+ reduction)
- CE: 6.31 → 1.5 (76% drop)
- D: 2.02 → 1.58 (22% drop)
- SAE: 0.65 → 0.58 (stable)

---

## What Happened

Training died at step ~500 during `model.save_pretrained()`. GPU was at 85.5GB/130GB — the save operation needed extra memory to serialize 5.1B LoRA weights, causing OOM.

**Fixes applied:**
1. `save_every` changed from 500 → 1000 (less frequent saves)
2. Pre-save: `torch.cuda.empty_cache()` + `gc.collect()` + `torch.cuda.synchronize()`
3. CPU offload: `model.to('cpu')` before save, `model.to('cuda')` after
4. Try/except/finally around save to ensure GPU return even on failure
5. Auto-resume logic: detects latest checkpoint on startup

**Checkpoint status:**
- Step 500: EMPTY (only README.md, no weights — save failed mid-write)
- Step 1000: Not yet reached
- No valid checkpoints exist — restart from scratch

---

## Quick Status Commands

```bash
# Latest 5 steps
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'grep "Step [0-9]*.*Loss" /mnt/bigssd/train_lora_sae_teacher_v1_restart.log | tail -5'

# Process alive check
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'ps -p 590094 -o pid,comm,etime,pcpu,pmem 2>/dev/null || echo "PROCESS_DEAD"'

# Log tail (last 20 lines)
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'tail -20 /mnt/bigssd/train_lora_sae_teacher_v1_restart.log'

# Check for OOM kills
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'dmesg | grep -i "killed process" | tail -3'

# GPU status
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits'
```

---

## File Locations

| File | Path |
|------|------|
| Training log | `/mnt/bigssd/train_lora_sae_teacher_v1_restart.log` |
| Training script | `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` |
| Checkpoints | `/data/SpecForge/custom_dflash/checkpoints/` |
| Teacher cache | `/mnt/bigssd/teacher_hidden_states_v3/` |
| Model | `/data/models/Qwen3.6-27B-Uncensored/` |
| Teacher | `/data/models/FrankenV8-Final/` |

---

## Upstream Sync Status (May 6)

**Cherry-picked from upstream:**
- ✓ grok-4.3 model addition
- ✓ deepseek-v4-pro model addition
- ✓ arcee temperature + compression overrides
- ✓ aux provider compression context length fix
- ✓ hindsight API append mode + dedupe

**Deferred (conflict risk with custom training code):**
- ○ kanban max_spawn config
- ○ kanban failure counter unification
- ○ SSE token batching fix
- ○ providers pluggable architecture

**Skipped (i18n/docs):**
- ✗ Turkish/Ukrainian/French/Chinese locales
- ✗ README translations
- ✗ Open WebUI/Ollama guides

---

## Critical Notes

- **DGX SSH times out during heavy loads** — this is expected. Use `process_poll` instead of SSH when training is active.
- **No screen session** — training runs via nohup directly. PID 590094.
- **First checkpoint at step 1000** — ~8 hours from now. Watch for OOM.
- **If training dies again:** Check `/mnt/bigssd/train_lora_sae_teacher_v1_restart.log` for "Checkpoint save failed" or OOM signs.
