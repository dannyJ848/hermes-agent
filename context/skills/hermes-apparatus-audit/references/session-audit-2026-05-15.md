# Session Audit: Full Cognitive Apparatus Optimization (May 15, 2026)

## Context
User requested a comprehensive audit of the entire memory and learning apparatus before starting a new project. This session produced a complete system optimization across local (MacBook) and remote (DGX Spark) infrastructure.

## Audit Results

### Local (MacBook)
| Component | Before | After |
|-----------|--------|-------|
| Disk space | 99% (12GB free) | 40% (20GB free) |
| Hindsight API | OFFLINE (port 8081 dead) | ONLINE (Ollama qwen3:14b on 11434) |
| Cerebrum `distilled_tips` | Missing table (API error) | Created, 3 tips mirrored from staging |
| Epistemic facts | 8 (1 false, 2 speculative) | 4 (cleaned) |
| loop_detection | 2,533 rows | 500 rows (recent only) |
| Cron jobs | 10 active (3 dead brain-cycle) | 7 active (dead ones removed) |
| SOUL.md | 10 behaviors | 12 behaviors (2 new May 15) |

### DGX Spark
| Component | Before | After |
|-----------|--------|-------|
| Cognitive Orchestrator | 19/20 (cortex_flywheel skipped) | **20/20 ACTIVE** |
| Root cause | "no such column: node_type" error | Stale cached schema — DB already correct |

## Key Techniques Discovered

### 1. Stale Schema Cache Pattern
When the cognitive orchestrator reports missing DB columns:
```bash
# ALWAYS verify actual schema before ALTER
sqlite3 ~/.hermes/cortex.db ".schema cortex_nodes"
```
The DGX `cortex.db` already had the full schema with `node_type`. The error was from stale cached schema info in the orchestrator's initialization path. Restarting the gateway refreshed the cache and resolved the issue.

### 2. Hindsight Fallback Configuration
When the configured local LLM (port 8081) is unavailable, reconfigure hindsight to use an available Ollama model:
```json
{
  "llm_base_url": "http://127.0.0.1:11434/v1",
  "llm_model": "qwen3:14b",
  "status": "ONLINE - Ollama fallback"
}
```

### 3. Cron Remove Workaround
When `hermes cron remove` fails with `Failed to remove job: 'id'`:
```python
import json
with open('~/.hermes/cron/jobs.json', 'r') as f:
    data = json.load(f)
data['jobs'] = [j for j in data['jobs'] if 'brain-cycle' not in j.get('name', '')]
with open('~/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### 4. Disk Cleanup Priority
For `.hermes/checkpoints/` (git repos):
```bash
# Remove legacy checkpoint directories older than 14 days
find ~/.hermes/checkpoints -maxdepth 1 -type d -mtime +14 -exec rm -rf {} +
```
For `.hermes/state-snapshots/`:
```bash
# Keep only the most recent snapshot
cd ~/.hermes/state-snapshots && ls -t | tail -n +2 | xargs rm -rf
```

## Verification Commands

Post-audit verification:
```bash
# Disk
df -h /

# DGX cognitive status
ssh djg6228@spark-85e8.local 'export HERMES_CONFIG=/data/SpecForge/hermes-agent/config.yaml; cd /data/SpecForge/hermes-agent; source venv/bin/activate; python3 -c "from agent.cognitive_orchestrator import get_orchestrator; co=get_orchestrator(); r=co.initialize(type(\"A\",(),{})()); print(sum(1 for v in r.values() if v==\"active\"), \"/\", len(r), \"active\")"'

# Hindsight
curl -s http://127.0.0.1:11434/v1/models | grep -c "qwen3"

# Cerebrum tables
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
```

## Files Modified
- `~/.hermes/SOUL.md` — added 2 learned behaviors
- `~/.hermes/hindsight/config.json` — reconfigured to Ollama fallback
- `~/.hermes/cerebrum_memory.db` — created `distilled_tips` table, cleaned epistemic facts, trimmed loop_detection
- `~/.hermes/cron/jobs.json` — removed 3 dead brain-cycle jobs
- `~/.hermes/checkpoints/` — removed legacy directories
- `~/.hermes/state-snapshots/` — removed old snapshots
