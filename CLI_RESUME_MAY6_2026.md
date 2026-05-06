# CLI Resume — Qwen 27B Training + Learning Apparatus + Hermes Harness

**Generated:** May 6, 2026 12:35 UTC
**For:** New Hermes Agent CLI session
**Branch:** `qwen27b-training-artifacts-may3-2026`
**Commit:** `46ee245e4` (with upstream cherry-picks + enhancements)

---

## Training Status (RESTARTED — Step 0/4000)

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

**Cherry-picked from upstream (applied May 6 morning):**
- ✓ grok-4.3 model addition
- ✓ deepseek-v4-pro model addition
- ✓ arcee temperature + compression overrides
- ✓ aux provider compression context length fix
- ✓ hindsight API append mode + dedupe

**Applied May 6 afternoon (deferred updates):**
- ✓ kanban max_spawn config (f0d278412)
- ✓ SSE token batching + error handling (3188e63b0)
- ✓ kanban failure counter unification (1fc8733a6) + diagnostics engine (f67063ba8)

**Applied May 6 evening (new features):**
- ✓ Per-capability backend selection (bf4e50214) — web_search/web_extract split
- ✓ Hook context spill to disk (b6c53ef0b) — prevents context overflow
- ✓ Kanban task_runs.summary (3f9729741) — better task visibility
- ✓ Cron no_agent mode (3db6b9cc8) — script-only cron jobs

**Skipped (structural conflicts):**
- ✗ providers pluggable architecture (9022804d7) — our branch deleted providers/ directory

**Skipped (i18n/docs):**
- ✗ Turkish/Ukrainian/French/Chinese locales
- ✗ README translations
- ✗ Open WebUI/Ollama guides

---

## Learning Apparatus Status

| Component | Status | Count |
|-----------|--------|-------|
| Cerebrum tips | ✓ | 1900 |
| ELO entries | ✓ | 1870 |
| Mastery scores | ✓ | 38 |
| Reasoning traces | ✓ | 68 |
| Error patterns | ✓ | 3 (78 occurrences) |
| Tool mastery tracked | ✓ | 167 tools |
| Skills | ✓ | 360 total, 0 broken |
| Cortex nodes | ✓ | 100 (synced from cerebrum) |

**Enhancements (May 6):**
- Adaptive ELO K-factor (K=40 → 20 after 10 matches)
- Tool-specific mastery tracking
- Failure-to-success pipeline
- Cross-domain transfer tracker
- Session compression quality tracker
- Tip velocity tracker (14 days history)

---

## Hermes Harness — Workflow Helpers

Created to work around weak tools:

| Helper | Replaces | Success Rate |
|--------|----------|-------------|
| `~/.hermes/scripts/cron_helper.py` | cronjob tool | 13% → CLI |
| `~/.hermes/scripts/patch_helper.py` | patch tool | 59% → validated |
| `~/.hermes/scripts/skill_helper.py` | skill_manage | 49% → YAML-safe |

**Usage:**
```bash
python3 ~/.hermes/scripts/cron_helper.py list
python3 ~/.hermes/scripts/cron_helper.py remove <job_name>
python3 ~/.hermes/scripts/patch_helper.py <file> <old> <new>
python3 ~/.hermes/scripts/skill_helper.py create <name> <category> <content>
```

---

## Critical Notes

- **DGX SSH times out during heavy loads** — this is expected. Use `process_poll` instead of SSH when training is active.
- **No screen session** — training runs via nohup directly. PID 590094.
- **First checkpoint at step 1000** — ~8 hours from now. Watch for OOM.
- **If training dies again:** Check `/mnt/bigssd/train_lora_sae_teacher_v1_restart.log` for "Checkpoint save failed" or OOM signs.
- **Use helpers for cron/patch/skill ops** — avoid weak tools directly.


---

## Hermes Source Enhancements (May 6)

**New monitoring tools:**
| Tool | Purpose | Location |
|------|---------|----------|
| `tool_intelligence_reporter.py` | Tracks per-tool success rates | `tools/` |
| `context_pressure_gauge.py` | Monitors token pressure, spills at >80% | `tools/` |
| `adaptive_timeout.py` | Calculates timeouts from historical performance | `tools/` |

**Database tables:**
| Table | Purpose |
|-------|---------|
| `circuit_breaker` | Tracks consecutive failures per tool |
| `context_pressure` | Tracks token usage over time |

**Integration points:**
- `hermes_cli/plugins.py` — `dispatch_tool()` now tracks performance
- Circuit breaker auto-disables tools after 5 consecutive failures
- Adaptive timeout = 3x average + 20% buffer

**Usage:**
```bash
python3 tools/tool_intelligence_reporter.py  # View success rates
python3 tools/adaptive_timeout.py            # View adaptive timeouts
python3 tools/context_pressure_gauge.py    # Test pressure gauge
```
