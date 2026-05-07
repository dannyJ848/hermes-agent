# Qwen 27B Training — Master Document
**Last Updated:** May 6, 2026 21:33 UTC
**Status:** RUNNING — PID 881997, Step 40/4000
**Branch:** qwen27b-training-artifacts-may3-2026
**Commit:** 744e9cb5d

## Current Training State
| Attribute | Value |
|-----------|-------|
| PID | 881997 |
| Step | 40/4000 (1.0%) |
| Status | RUNNING — ACTIVE |
| Loss | 4.81 (CE:4.51 D:1.47 SAE:0.59) |
| GPU | 85.3GB / 130GB |
| Runtime | 33 minutes |
| DGX | 10.0.0.171 (djg6228/6228) |
| LoRA | r=1024, alpha=2048 |
| Trainable | 5.1B params (15.9% of 32B) |
| Config | max_steps=4000, save_every=500, batch=1, grad_accum=4 |
| Log | `/mnt/bigssd/train_lora_sae_teacher_v1_restart.log` |
| Script | `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` |

**Loss trajectory:**
- Step 20: 5.79 → Step 40: 4.81 = **17% reduction in 20 steps**
- All 3 losses active (CE + D + SAE)

**ETA to step 500 (first checkpoint test):** ~4 hours

## Critical Fixes Applied (May 6, 2026)

### Fix #1: Checkpoint Save OOM (CRASHED at step 999)
- **Root cause:** `model.to('cpu')` moved 85GB to system RAM → OOM killer killed PID 590094
- **Fix:** Save only LoRA adapter params (param.detach().cpu()), no full model move
- **Impact:** ~5GB vs 85GB — safe on 128GB RAM

### Fix #2: Resume Bug (PeftModel.from_pretrained)
- **Bug:** `model = model.from_pretrained(ckpt_path)` fails with `TypeError: missing required positional argument: 'model_id'`
- **Fix:** Use `hasattr(model, 'load_adapter')` check + `PeftModel.from_pretrained(model, ckpt_path)`

### Fix #3: Empty Checkpoint Dir
- **Action:** Deleted `/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_1000` (empty, failed save)
- **Result:** Training starts from step 0 with clean state

## Systems Built This Session

### BUILT ✓
| System | File | Status |
|--------|------|--------|
| Cortex Memory (unified_context.db) | `~/.hermes/unified_context.db` | ✓ LIVE — 19 keys |
| Tiered Memory Engine | `hermes_cli/subconscious/tiered_memory.py` | ✓ LIVE |
| Memory Daemon | `hermes_cli/subconscious/memory_daemon.py` | ✓ LIVE |
| Learning Brain Plugin | `plugins/learning-brain/` | ✓ LIVE — hooks wired |
| LLM Judge | `plugins/learning-brain/llm_judge.py` | ✓ LIVE — deepseek-v4-pro |
| Self-Audit Engine | `hermes_cli/subconscious/self_audit_engine.py` | ✓ LIVE |
| Harness Enhancer | `hermes_cli/subconscious/hermes_harness_enhancer.py` | ✓ LIVE |
| Instant Context | `hermes_cli/instant_context.py` | ✓ LIVE |
| Session Bootstrap | `hermes_cli/session_bootstrap.py` | ✓ LIVE |
| Complete Resume | `CLI_RESUME_COMPLETE_MAY6_2026.md` | ✓ LIVE |

### PENDING ✗
| System | Status | Why Missing |
|--------|--------|-------------|
| Memory→Cortex Offload Bridge | ✗ NOT BUILT | Ran out of turns, training crash took priority |
| Error Pattern Miner | ✗ NOT BUILT | Pending #5 in harness enhancer |
| Multi-Step Validator | ✗ NOT BUILT | Pending #6 |
| Context Window Guard | ✗ NOT BUILT | Pending #7 |
| Distillation Quality Gate | ✗ NOT BUILT | Pending #10 |

### PARTIALLY BUILT ⚠️
| System | Status | Issue |
|--------|--------|-------|
| **Skill Update** | ⚠️ DUPLICATED | Section 26 duplicated in `qwen27b-training-pipeline/SKILL.md`. Patch tool failed 3x, used sed workaround that left duplicates. |
| **Repo Push** | ⚠️ BLOCKED THEN FIXED | GitHub secret scanning blocked push (PAT in resume doc). Amended commit to redact PAT. |
| **Cortex PostgreSQL** | ⚠️ FALLBACK ONLY | COLD tier uses SQLite fallback, not real PostgreSQL. |

## Known Issues
- **Memory tool at 99%** (2477/2500 chars) — No auto-offload bridge. Manual replacement only.
- **Skill file corruption** — Section 26 duplicated. Needs manual cleanup.
- **SSH to DGX may timeout** during heavy model loading — expected behavior.

## File Locations
- Training script: `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py`
- Log: `/mnt/bigssd/train_lora_sae_teacher_v1_restart.log`
- Checkpoints: `/data/SpecForge/custom_dflash/checkpoints/`
- Cache: `/mnt/bigssd/teacher_cache/` (82K+ PKL files)
- Unified context: `~/.hermes/unified_context.db`

## Quick Status Commands
```bash
# Check process
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 djg6228@10.0.0.171 "ps -p 881997 -o pid,comm,etime,pcpu,pmem 2>/dev/null || echo 'PROCESS_DEAD'"

# Check log tail
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 djg6228@10.0.0.171 "tail -5 /mnt/bigssd/train_lora_sae_teacher_v1_restart.log"

# Check latest steps
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 djg6228@10.0.0.171 "grep -E 'Step [0-9]+.*Loss' /mnt/bigssd/train_lora_sae_teacher_v1_restart.log | tail -3"
```

## Configuration
- DGX: 10.0.0.171, djg6228/6228
- Repo: dannyJ848/hermes-agent, branch qwen27b-training-artifacts-may3-2026
- PAT: [REDACTED — see memory tool]

## Pending Tasks
1. **Checkpoint test at step 500** — Verify LoRA-only save works (no OOM)
2. **Fix skill file duplication** — Clean up section 26 in qwen27b-training-pipeline
3. **Build memory→cortex offload bridge** — Auto-offload when memory full
4. **Build error pattern miner** — From error_registry data
5. **Build multi-step validator** — Validate complex tool call sequences

---
*This resume is the single source of truth. Update it whenever state changes.*
