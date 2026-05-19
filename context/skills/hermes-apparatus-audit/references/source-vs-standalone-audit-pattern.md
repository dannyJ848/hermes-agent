# Source vs Standalone Audit Pattern

When the user asks "what was actually built into Hermes source?", run this systematic check.

## The Question

The user expects cognitive systems to be surgically integrated into Hermes source code, not built as standalone scripts. The exact quote:

> "so were you able to build into the hermes source everything that could be built into tangible enhancements for you?"

## Audit Commands

### 1. Count files in agent/ and tools/
```bash
ls ~/hermes-agent/agent/cognitive_*.py 2>/dev/null | wc -l
echo "cognitive modules in agent/"
ls ~/hermes-agent/tools/cognitive_*.py 2>/dev/null | wc -l
echo "cognitive tools in tools/"
```

### 2. Check wiring in run_agent.py
```bash
grep -n "cognitive\|iteration_engine\|self_evolution\|hook_manager\|register_hook" ~/hermes-agent/run_agent.py | head -20
```

### 3. Check plugin status
```bash
hermes plugins list 2>/dev/null | grep -E "cognitive-systems|learning-brain"
```

### 4. List standalone files
```bash
echo "Standalone scripts:"
ls ~/subconscious/*.py 2>/dev/null
ls /tmp/x_api.py 2>/dev/null
echo "Skills (not source code):"
ls ~/.hermes/skills/ 2>/dev/null | head -10
```

## Classification Framework

| Category | Location | Counts as "in source"? |
|----------|----------|----------------------|
| `agent/*.py` | `~/hermes-agent/agent/` | ✅ YES |
| `tools/*.py` | `~/hermes-agent/tools/` | ✅ YES |
| Plugin files | `~/.hermes/plugins/*/plugin.yaml` | ✅ YES (loaded by plugin system) |
| Skills | `~/.hermes/skills/*/` | ❌ NO (skill system, not source code) |
| Knowledge | `~/.hermes/knowledge/` | ❌ NO (data, not source code) |
| Standalone scripts | `/tmp/`, `~/subconscious/` | ❌ NO |
| Config | `~/.hermes/config.yaml` | ⚠️ PARTIAL (configures source, not source itself) |

## Response Template

**BUILT INTO HERMES SOURCE:**
- List each file in `agent/` and `tools/` with size and wiring points
- Show plugin status (enabled, loaded, verified)
- Show run_agent.py line numbers where hooks are called

**NOT BUILT INTO SOURCE (standalone only):**
- List each standalone script and why it's not in source
- List skills (explain skill system ≠ source code)
- List knowledge files (explain data ≠ source code)

**WHAT COULD BE INTEGRATED:**
- Identify which standalone scripts should become tools in `tools/`
- Identify which configs should be wired into `agent/auxiliary_client.py`
- Identify which credentials should be in `~/.hermes/config.yaml`

## Example from July 2026 Session

**BUILT INTO SOURCE:**
- `iteration_engine.py` — 28KB, wired at run_agent.py lines 10045-10936
- `self_evolution.py` — 18KB, Elo tournaments + tip evolution
- `cognitive_infrastructure_*.py` — 3 files, hook registration
- `tools/vision_tools.py` — 44KB, vision analysis
- `cognitive-systems` plugin v2.0.0 — 5 hooks registered

**NOT BUILT INTO SOURCE:**
- `x_api.py` — `/tmp/x_api.py` (NOT `tools/x_api.py`)
- 10 new skills — `~/.hermes/skills/` (skill system, not source)
- Knowledge files — `~/.hermes/knowledge/` (data, not source)
- Twitter cookies — ephemeral, not in agent config

**WHAT COULD BE INTEGRATED:**
1. `x_api.py` → `tools/x_api.py` (register as `x_tweet_fetch`, `x_search` tools)
2. GLM-5V-Turbo config → `agent/auxiliary_client.py` (vision provider)
3. Twitter cookies → `~/.hermes/config.yaml` or env var
4. CLAUDE.md rules → inject into `delegate_task` context

## Key Pitfall: Don't Confuse Skills with Source

Skills in `~/.hermes/skills/` are **behavioral knowledge**, not source code. They tell the agent HOW to do things. They don't add new capabilities to the agent's runtime.

Tools in `~/hermes-agent/tools/` are **runtime capabilities**. They add new functions the agent can call.

When the user asks about "building into Hermes source", they mean runtime capabilities (tools, agent modules, plugins), not behavioral knowledge (skills, knowledge files).
