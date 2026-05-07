# CLI Resume — Complete Session State
**Generated:** May 6, 2026 21:30 UTC
**Session:** Hermes Agent — Qwen 27B Training + Cortex Memory + Learning Brain
**Commit:** adf85f3d0
**Branch:** qwen27b-training-artifacts-may3-2026

---

## [CRITICAL] Training Status
| Attribute | Value |
|-----------|-------|
| PID | 881997 |
| Step | 0/4000 (restarted from scratch after crash) |
| Status | RUNNING — model loading in progress |
| GPU | Loading (will be ~85GB when running) |
| DGX | 10.0.0.171 (djg6228/6228) |
| LoRA | r=1024, alpha=2048 |
| Trainable | 5.1B params (15.9% of 32B) |
| Config | max_steps=4000, save_every=500, batch=1, grad_accum=4 |
| Log | `/mnt/bigssd/train_lora_sae_teacher_v1_restart.log` |
| Script | `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` |

**Check status:**
```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 djg6228@10.0.0.171 "ps -p 881997 -o pid,comm,etime,pcpu,pmem 2>/dev/null || echo 'PROCESS_DEAD'"
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 djg6228@10.0.0.171 "tail -5 /mnt/bigssd/train_lora_sae_teacher_v1_restart.log"
```

**Crash History (May 6, 2026):**
- Step 999/4000: OOM during checkpoint save
- Fix #1: Save LoRA adapters only (param.detach().cpu()), no full model CPU move
- Fix #2: Resume bug — `PeftModel.from_pretrained(model, ckpt_path)` with `load_adapter` fallback
- Empty checkpoint dir deleted, training restarted from step 0

---

## [SYSTEMS BUILT THIS SESSION]

### 1. Cortex Memory System (Unified DB)
**File:** `~/.hermes/unified_context.db` (SQLite)
**Purpose:** Single source of truth for all persistent state

**Schema:**
```sql
CREATE TABLE context (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);
```

**Key entries:**
- `training_status`, `training_step`, `training_pid`, `training_gpu`, `training_loss`
- `crash_cause`, `crash_fix_1`, `crash_fix_2`
- `tiered_memory_hot_utilization`, `tiered_memory_warm_count`, `tiered_memory_cold_count`
- `deepseek_judge_status`, `last_commit`

**Access:**
```python
import sqlite3
conn = sqlite3.connect('~/.hermes/unified_context.db')
c = conn.cursor()
c.execute("SELECT value FROM context WHERE key='training_status'")
```

### 2. Tiered Memory System
**File:** `hermes_cli/subconscious/tiered_memory.py`
**Daemon:** `hermes_cli/subconscious/memory_daemon.py`

**Three tiers:**
- **HOT:** `~/.hermes/memory.json` (2,500 char limit, immediate context)
- **WARM:** `~/.hermes/cerebrum_memory.db` (SQLite staging for tips awaiting LLM judge)
- **COLD:** Cortex PostgreSQL/SQLite fallback (Elo-rated archive)

**Current state:**
- HOT: 72.4% utilized (8 entries)
- WARM: 0 unrated tips
- COLD: 0 high-performers (fallback SQLite)

**Commands:**
```bash
python3 hermes_cli/subconscious/memory_daemon.py --stats
python3 hermes_cli/subconscious/memory_daemon.py --offload
python3 hermes_cli/subconscious/memory_daemon.py --promote
```

### 3. Learning Brain Plugin
**Path:** `plugins/learning-brain/`
**Files:**
- `__init__.py` — Plugin registration, hooks, judge singleton
- `context_updater.py` — DB updates, session continuity, tips_learned
- `llm_judge.py` — DeepSeek V4 Pro integration, JSON extraction fix
- `error_registry.py` — Failure logging, pattern matching
- `self_audit_engine.py` — Loop detection, token waste tracking, preflight checks

**Hooks active:**
- `pre_tool_call` — Circuit breaker for weak tools, preflight validation
- `post_tool_call` — Tip extraction, LLM judge evaluation, error logging
- `on_session_start` — Context hydration from unified DB
- `on_session_end` — State flush to DB

**LLM Judge routing:**
- Score < 0.6 → `error_registry`
- Score ≥ 0.7 + actionable → `session_continuity.tips_learned`

### 4. Self-Audit Engine
**File:** `hermes_cli/subconscious/self_audit_engine.py`

**Features:**
- Loop detection (hash-based sliding window, alerts on 3+ identical calls)
- Token waste tracker (logs failed calls consuming >100 tokens)
- Pre-flight check (validates required args before expensive calls)
- Recovery suggester (pattern-matches errors to known workarounds)

**Integration:** Wired into learning-brain plugin hooks

### 5. Hermes Harness Enhancer
**File:** `hermes_cli/subconscious/hermes_harness_enhancer.py`

**Gap analysis identified 10 missing tools:**
1. loop_detector (built in self_audit_engine)
2. recovery_suggester (built in self_audit_engine)
3. preflight_checker (built in self_audit_engine)
4. token_waste_tracker (built in self_audit_engine)
5. error_pattern_miner (pending)
6. multi_step_validator (pending)
7. context_window_guard (pending)
8. tool_circuit_breaker (wired in learning-brain)
9. session_continuity_manager (wired in learning-brain)
10. distillation_quality_gate (pending)

### 6. Instant Context CLI
**File:** `hermes_cli/instant_context.py`
**Purpose:** One-command status snapshot for any new CLI session

**Shows:**
- Training state (step, loss, GPU, PID)
- Tool intelligence (success rates, circuit states)
- Recent errors (with suggested fixes)
- Tiered memory utilization (HOT/WARM/COLD bars)
- Session continuity (last 3 tips learned)

**Run:**
```bash
python3 hermes_cli/instant_context.py
```

---

## [FILE LOCATIONS]

**Core systems:**
- `~/.hermes/unified_context.db` — Cortex unified database
- `~/.hermes/memory.json` — HOT tier (2,500 char limit)
- `~/.hermes/cerebrum_memory.db` — WARM tier (SQLite)
- `hermes_cli/instant_context.py` — CLI status snapshot
- `hermes_cli/subconscious/tiered_memory.py` — Tiered memory engine
- `hermes_cli/subconscious/memory_daemon.py` — Background daemon
- `hermes_cli/subconscious/self_audit_engine.py` — Self-audit system
- `hermes_cli/subconscious/hermes_harness_enhancer.py` — Gap analysis

**Plugin:**
- `plugins/learning-brain/__init__.py` — Main plugin
- `plugins/learning-brain/context_updater.py` — DB updater
- `plugins/learning-brain/llm_judge.py` — DeepSeek judge
- `plugins/learning-brain/error_registry.py` — Error logging

**Resume docs:**
- `MASTER_DOC.md` — Training master document
- `CLI_RESUME_MAY6_2026.md` — Session resume (May 6)
- `CLI_RESUME_MAY6_CRASH.md` — Crash recovery doc
- `CLI_RESUME_COMPLETE_MAY6_2026.md` — This file

**Skills:**
- `qwen27b-training-pipeline` — Training pipeline skill
- `tiered-memory-system` — Memory management skill

---

## [QUICK COMMANDS FOR NEW CLI]

```bash
# 1. Check everything at once
python3 hermes_cli/instant_context.py

# 2. Check training on DGX
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 djg6228@10.0.0.171 "tail -5 /mnt/bigssd/train_lora_sae_teacher_v1_restart.log"

# 3. Check memory daemon
python3 hermes_cli/subconscious/memory_daemon.py --stats

# 4. Check self-audit
python3 hermes_cli/subconscious/self_audit_engine.py

# 5. Update repo
git pull origin qwen27b-training-artifacts-may3-2026
```

---

## [CONFIGURATION]

**DGX access:**
- IP: 10.0.0.171
- User: djg6228
- Pass: 6228
- SSH: `ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171`

**GitHub:**
- Repo: dannyJ848/hermes-agent
- PAT: [REDACTED — see memory tool]
- Branch: qwen27b-training-artifacts-may3-2026

**DeepSeek Judge:**
- Model: deepseek-v4-pro
- Status: Active in learning-brain plugin
- Routing: score<0.6→error_registry, score≥0.7→tips_learned

---

## [PENDING TASKS]

1. **Checkpoint test at step 500** — Verify LoRA-only save works (no OOM)
2. **Memory offload bridge** — Auto-offload from HOT→WARM→COLD when memory full
3. **Error pattern miner** — Build from error_registry data
4. **Multi-step validator** — Validate complex tool call sequences
5. **Context window guard** — Prevent reasoning degradation in long sessions

---

*This resume is the single source of truth for session handoff. Update it whenever state changes.*
