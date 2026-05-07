# CLI Resume Document — May 6, 2026 (CRASH RECOVERY)

## CRITICAL: Training Status
- **Status:** CRASHED at step 999/4000 (25%)
- **Crash point:** Checkpoint save at step 1000
- **Crash cause:** System OOM during `model.to('cpu')` — moved 85GB to RAM, OOM killer killed PID 590094
- **Crash fix:** Save LoRA adapters only (small tensors), no full model CPU move
- **Fix applied:** `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` patched
- **Resume script:** `/tmp/resume_training.sh` on DGX
- **Next checkpoint:** Step 1500 (will test if fix works)

## Training Configuration (Verified)
- Model: Qwen 27B LoRA (rank=1024)
- max_steps: 4000 (live read in loop, stops at 4000)
- save_every: 500
- warmup_steps: 400
- Step duration: 30.2s (not 5min — log interval is 10 steps)
- ETA to 4K: ~28h (was ~26h before crash)
- GPU: 85.3GB / 130GB stable
- Loss at crash: ~2.02 (CE:1.61, D:1.99, SAE:0.60)

## Checkpoint History
- Step 0: FrankenV8-Final loaded (restart from previous checkpoint)
- Step 500: NOT saved (save_every changed from 1000 to 500 mid-run)
- Step 1000: **FAILED** — empty checkpoint dir, process killed by OOM
- Fix: LoRA-only save (no model.to('cpu'))

## Crash Recovery Plan
1. Run `/tmp/resume_training.sh` on DGX
2. Script auto-detects latest checkpoint (step 0 FrankenV8 since step 1000 is empty)
3. Training resumes with fixed save logic
4. Next save at step 500 will test the fix
5. If step 500 save succeeds, continue to 4000

## Unified Context DB (instant_context.py)
Run: `python3 hermes_cli/instant_context.py`
Keys updated:
- training_status: CRASHED - checkpoint save OOM
- training_step: 999/4000 (crashed at step 1000 save)
- crash_cause: System OOM during model.to(cpu)
- crash_fix: Save LoRA adapters only
- checkpoint_step_1000_status: FAILED - empty dir
- training_resume_script: /tmp/resume_training.sh

## Tiered Memory System
- HOT: 72.4% (8 entries)
- WARM: 0 unrated tips
- COLD: SQLite fallback (0 high-performers)
- Daemon: `python3 hermes_cli/subconscious/memory_daemon.py --stats`

## LLM Judge (deepseek-v4-pro)
- Active in learning-brain plugin
- Auto-evaluates tips: score<0.6 → error_registry; score≥0.7 → session_continuity.tips_learned
- Fixed JSON extraction: response_format=json_object, 2000 tokens

## Self-Audit Engine (Wired into Plugin)
- Pre-flight: blocks missing args (patch without old_string)
- Loop detection: 3+ identical calls → BLOCK
- Token waste: logs failed/repeated calls
- Tested: loop detected, preflight blocks, waste tracked

## Learning-Brain Plugin
- Hooks: pre_tool_call, post_tool_call, on_session_start, on_session_end
- Self-audit + LLM judge both wired
- Commit: 92aff7be1 (118 ahead of remote)

## Repo Status
- Branch: qwen27b-training-artifacts-may3-2026
- Commit: 92aff7be1
- 118 commits ahead of remote
- Source: dannyJ848/hermes-agent (not upstream)

## Recovery Commands
```bash
# On DGX:
/tmp/resume_training.sh

# Local instant context:
python3 hermes_cli/instant_context.py

# Memory daemon:
python3 hermes_cli/subconscious/memory_daemon.py --stats

# Self-audit:
python3 hermes_cli/subconscious/self_audit_engine.py
```
