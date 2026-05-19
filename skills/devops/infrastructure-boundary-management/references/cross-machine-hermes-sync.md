# Cross-Machine Hermes Sync — Session Detail

## Session Context
Date: May 14, 2026
Task: DGX Hermes deployment had only 21 tools vs MacBook's 103
Root cause: Evey plugins in `~/.hermes/plugins/` not synced, not enabled in config

## Discovery Path

1. **Tool count discrepancy identified**
   - MacBook: 103 tools from `get_tool_definitions()`
   - DGX: 21 tools
   - 63 tools missing

2. **Root cause: missing plugins**
   - Extra tools traced to `~/.hermes/plugins/` on MacBook
   - 43 plugin directories including evey-autonomy, evey-bridge, evey-research, etc.
   - DGX `/home/djg6228/.hermes/plugins/` existed but was empty

3. **First attempt: synced plugins but still 21 tools**
   - Used `rsync` to copy plugins to DGX
   - Still showed "Plugin discovery complete: 49 found, 7 enabled"
   - Debug showed all evey plugins being skipped: "not in plugins.enabled"

4. **Critical finding: config file location**
   - Edited `/data/SpecForge/hermes-agent/config.yaml` (repo config)
   - Hermes actually loads from `/home/djg6228/.hermes/config.yaml` (home config)
   - `get_config_path()` confirmed: home config takes precedence
   - Home config had NO `plugins` section at all

5. **Solution**
   - Added `plugins.enabled` and `plugins.disabled` to `~/.hermes/config.yaml`
   - Tool count jumped from 21 → 84

## Plugin-to-Tool Mapping (Key Plugins)

| Plugin | Tools Registered |
|--------|-----------------|
| evey-autonomy | autonomous_decide, autonomous_plan, autonomous_reflect |
| evey-bridge | claude_bridge_check, claude_bridge_message, claude_bridge_task |
| evey-cost-guard | cost_check, cost_set_budget, cost_analytics |
| evey-github | github_status, github_pr_status |
| evey-mesh | mesh_status, mesh_message, mesh_task, mesh_lock |
| evey-news | news_scan |
| evey-rag | knowledge_search, knowledge_stats |
| evey-research | web_research |
| evey-verification | verify_dns, verify_endpoint, verify_repo, verify_url |
| evey-watchdog | watchdog_heartbeat, watchdog_status |
| learning-brain | (hooks only, no tools) |

## Config Format

The working format (modern):
```yaml
plugins:
  disabled:
    - evey-eyes
    - evey-moltbook
  enabled:
    - evey-autonomy
    - evey-bridge
    # ... etc
```

The old format (deprecated for user plugins):
```yaml
plugins:
  - hermes_cli.plugins.memory
  - hermes_cli.plugins.skills
```

## Verification Commands

```bash
# Check which config is loaded
python3 -c "from hermes_cli.config import get_config_path; print(get_config_path())"

# Check plugin discovery with debug logging
python3 -c "
from hermes_cli.plugins import discover_plugins
import logging
logging.basicConfig(level=logging.DEBUG)
discover_plugins()
" 2>&1 | grep -E '(Skipping|enabled|not in plugins.enabled)'

# Count tools
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
print(f'Total: {len(tools)}')
"
```

## Post-Sync Errors (Expected)

After enabling all plugins, these non-critical errors appeared:
- `Failed to load plugin 'spotify': No module named 'plugins.spotify'` — missing dep, harmless
- `Failed to load plugin 'google_chat-platform': No module named 'gateway.status'` — missing dep, harmless
- `Tool registration REJECTED: 'web_extract' would shadow existing tool` — name collision between evey-research and core web tool
- `Failed to load plugin 'evey-honcho': No module named 'honcho_bridge'` — missing dep, harmless

These don't affect the 84 working tools.

## File Sync Verification (May 14, 2026)

After initial rsync, 10 critical agent modules were MISSING on DGX. They were created on MacBook May 13 but the rsync on May 14 missed them.

### Missing files discovered:
- `agent/adaptive_context_sculptor.py`
- `agent/attention_context_prioritizer.py`
- `agent/autonomous_experimentation.py`
- `agent/cognitive_orchestrator.py`
- `agent/cross_domain_transfer.py`
- `agent/epistemic_trust_scorer.py`
- `agent/predictive_failure_prevention.py`
- `agent/predictive_tool_oracle.py`
- `agent/self_evaluation_gate.py`
- `agent/unified_intelligence_engine.py`

### Verification command:
```bash
# Compare file lists between MacBook and DGX
find ~/hermes-agent -type f -not -path '*/venv/*' -not -path '*/node_modules/*' \
  -not -path '*/.git/*' -not -path '*/__pycache__/*' | sed 's|/Users/dannygomez/hermes-agent/||' | sort > /tmp/macbook_files.txt

ssh djg6228@spark "find /data/SpecForge/hermes-agent -type f -not -path '*/venv/*' \
  -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' \
  | sed 's|/data/SpecForge/hermes-agent/||' | sort" > /tmp/dgx_files.txt

# Find missing files
comm -23 /tmp/macbook_files.txt /tmp/dgx_files.txt
```

### Quick sync of missing files:
```bash
for f in agent/adaptive_context_sculptor.py agent/attention_context_prioritizer.py \
         agent/autonomous_experimentation.py agent/cognitive_orchestrator.py \
         agent/cross_domain_transfer.py agent/epistemic_trust_scorer.py \
         agent/predictive_failure_prevention.py agent/predictive_tool_oracle.py \
         agent/self_evaluation_gate.py agent/unified_intelligence_engine.py; do
    scp ~/hermes-agent/$f djg6228@spark:/data/SpecForge/hermes-agent/$f
done
```

### DGX-specific extra files (don't delete):
- `agent/dgx_integration.py` — DGX hardware integration
- `agent/dgx_learning_hook.py` — DGX-specific learning hooks
- `scripts/dgx_distillation_daemon.py` — Background distillation
- `scripts/dgx_session_exporter.py` — Session export for training

### Expected file counts after full sync:
| Metric | MacBook | DGX | Notes |
|--------|---------|-----|-------|
| Core Python files | ~1,756 | ~1,766 | DGX has +10 extra files |
| All source files | ~3,541 | ~3,527 | DGX lacks .git, .DS_Store |
| Skills | 357 | 357 | Synced |
| Knowledge files | 1,194 | 1,194 | Synced |
| Tools loaded | 103 | 97 | 6 API-dependent tools missing |

See `dgx-spark-qwen3-deployment/references/dgx-hermes-file-sync-verification.md` for the complete automated health check script.
