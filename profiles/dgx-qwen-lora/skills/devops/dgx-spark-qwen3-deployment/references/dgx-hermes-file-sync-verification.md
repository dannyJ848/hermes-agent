# DGX Hermes File Sync Verification

**Date:** May 14, 2026
**Context:** After initial rsync from MacBook to DGX, verify ALL critical files are present
**Problem:** 10 agent modules and config files were missing after sync, causing partial functionality

## Why Files Go Missing

1. **Rsync timing:** Files created on MacBook AFTER the last rsync won't be on DGX
2. **Git exclusions:** `.gitignore` patterns may skip files you need
3. **Different Python versions:** `__pycache__` files differ (arm64 vs x86_64)
4. **DGX-specific files:** DGX may have extra files (dgx_integration.py) not on MacBook

## Quick Verification

```bash
# Count core Python files (excluding deps)
find /data/SpecForge/hermes-agent -type f -name '*.py' \
  -not -path '*/venv/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/.pytest_cache/*' | wc -l
# Should be ~1750+ (MacBook has ~1756, DGX has ~1766 with extras)

# Count all source files
find /data/SpecForge/hermes-agent -type f \
  -not -path '*/venv/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/.pytest_cache/*' | wc -l
# Should be ~3500+ (MacBook: 3541, DGX: 3527)
```

## Deep Verification: Compare File Lists

```bash
# On MacBook — generate file list
find ~/hermes-agent -type f \
  -not -path '*/venv/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/.pytest_cache/*' \
  | sed 's|/Users/dannygomez/hermes-agent/||' | sort > /tmp/macbook_files.txt

# On DGX — generate file list
find /data/SpecForge/hermes-agent -type f \
  -not -path '*/venv/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/.pytest_cache/*' \
  | sed 's|/data/SpecForge/hermes-agent/||' | sort > /tmp/dgx_files.txt

# Find missing files
comm -23 /tmp/macbook_files.txt /tmp/dgx_files.txt > /tmp/missing_on_dgx.txt
comm -13 /tmp/macbook_files.txt /tmp/dgx_files.txt > /tmp/extra_on_dgx.txt

echo "Missing on DGX: $(wc -l < /tmp/missing_on_dgx.txt) files"
echo "Extra on DGX: $(wc -l < /tmp/extra_on_dgx.txt) files"
```

## Critical Files to Check

These agent modules are essential for full cognitive functionality:

| File | Purpose |
|------|---------|
| agent/adaptive_context_sculptor.py | Dynamic context window management |
| agent/attention_context_prioritizer.py | Attention-based context ranking |
| agent/autonomous_experimentation.py | Self-directed learning loops |
| agent/cognitive_orchestrator.py | Meta-cognitive coordination |
| agent/cross_domain_transfer.py | Skill transfer between domains |
| agent/epistemic_trust_scorer.py | Memory fact trust scoring |
| agent/predictive_failure_prevention.py | Proactive error detection |
| agent/predictive_tool_oracle.py | Tool outcome prediction |
| agent/self_evaluation_gate.py | Output quality gating |
| agent/unified_intelligence_engine.py | Cross-module integration |

```bash
# Verify all critical files exist
for f in adaptive_context_sculptor.py attention_context_prioritizer.py autonomous_experimentation.py cognitive_orchestrator.py cross_domain_transfer.py epistemic_trust_scorer.py predictive_failure_prevention.py predictive_tool_oracle.py self_evaluation_gate.py unified_intelligence_engine.py; do
    if [ -f /data/SpecForge/hermes-agent/agent/$f ]; then
        echo "✓ $f"
    else
        echo "✗ MISSING: $f"
    fi
done
```

## Sync Missing Files

```bash
# On MacBook — sync missing files individually
for f in agent/adaptive_context_sculptor.py agent/attention_context_prioritizer.py ...; do
    scp ~/hermes-agent/$f djg6228@spark:/data/SpecForge/hermes-agent/$f
done

# Or bulk sync the agent directory
rsync -avz ~/hermes-agent/agent/ djg6228@spark:/data/SpecForge/hermes-agent/agent/

# Or full re-sync (careful — overwrites DGX-specific files)
rsync -avz --exclude='.git' --exclude='venv' --exclude='node_modules' \
  ~/hermes-agent/ djg6228@spark:/data/SpecForge/hermes-agent/
```

## Config and Data Sync

```bash
# Sync Hermes home directory (skills, knowledge, memory)
rsync -avz ~/.hermes/skills/ djg6228@spark:/home/djg6228/.hermes/skills/
rsync -avz ~/.hermes/knowledge/ djg6228@spark:/home/djg6228/.hermes/knowledge/

# Sync .env file (API credentials)
scp ~/.hermes/.env djg6228@spark:/home/djg6228/.hermes/.env

# Sync config (but review first — DGX needs different paths)
# DON'T blindly copy config.yaml — DGX has different model paths and provider URLs
```

## Tool Count Verification

```bash
cd /data/SpecForge/hermes-agent
venv/bin/python -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
print(f'Total tools: {len(tools)}')

# Count by category
categories = {}
for t in tools:
    name = t.get('function',{}).get('name','')
    cat = name.split('_')[0] if '_' in name else 'other'
    categories[cat] = categories.get(cat, 0) + 1

for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f'  {cat}: {count}')
"
```

**Expected:** 97 tools on DGX (vs 103 on MacBook — 6 API-dependent tools missing)

## What the Counts Mean

| Tool Count | Meaning |
|-----------|---------|
| 21 | Default minimal config — no plugins enabled |
| 84 | Plugins enabled but no web APIs |
| 87 | + web_search, web_extract (Brave/Firecrawl keys) |
| 97 | + browser tools (Node.js + agent-browser installed) |
| 103 | MacBook full (has cronjob, Feishu, video_analyze) |

## DGX-Specific Extra Files

DGX has files NOT on MacBook (don't delete these):

| File | Purpose |
|------|---------|
| agent/dgx_integration.py | DGX hardware integration |
| agent/dgx_learning_hook.py | DGX-specific learning hooks |
| scripts/dgx_distillation_daemon.py | Background distillation |
| scripts/dgx_session_exporter.py | Session export for training |
| scripts/training_orchestrator.py | Training coordination |

## Automated Health Check Script

```bash
#!/bin/bash
# save as /tmp/hermes_health_check.sh on DGX

echo "=== Hermes Health Check ==="

cd /data/SpecForge/hermes-agent

# 1. Check core files
echo "Core files:"
for f in agent/adaptive_context_sculptor.py agent/cognitive_orchestrator.py agent/self_evaluation_gate.py; do
    [ -f "$f" ] && echo "  ✓ $f" || echo "  ✗ MISSING: $f"
done

# 2. Check tool count
echo ""
echo "Tool count:"
venv/bin/python -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
print(f'  {len(tools)} tools loaded')
if len(tools) < 90:
    print('  ⚠️ LOW — check plugin config and API keys')
else:
    print('  ✅ Good')
"

# 3. Check browser tools
echo ""
echo "Browser tools:"
venv/bin/python -c "
from tools.browser_tool import check_browser_requirements
print(f'  Browser available: {check_browser_requirements()}')
"

# 4. Check Node.js
echo ""
echo "Node.js:"
which node 2>/dev/null && node --version || echo "  ✗ Not in PATH"

# 5. Check config location
echo ""
echo "Config:"
venv/bin/python -c "
from hermes_cli.config import get_config_path
print(f'  {get_config_path()}')
"

echo ""
echo "=== Done ==="
```
