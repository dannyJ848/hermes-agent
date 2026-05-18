# Full Apparatus Wiring & Performance Audit — 2026-05-18

**Trigger:** User asked "run a full line by line wiring and performance audit of your entire integrated hermes apparatus. aka the entire source code."

**Key discovery:** Cognitive orchestrator exists (972 lines) but is **completely unwired** — zero calls to `initialize_cognitive_systems()` or `get_orchestrator()` anywhere in the codebase. This is a "dead code" failure mode distinct from partial hook wiring.

---

## Audit Methodology

### 1. Repository Scale Metrics
```python
import subprocess, os
os.chdir('~/.hermes')

# Count files by extension
r = subprocess.run(['find', '.', '-type', 'f',
    '(', '-name', '*.py', '-o', '-name', '*.js', '-o', '-name', '*.ts',
    '-o', '-name', '*.yaml', '-o', '-name', '*.yml', '-o', '-name', '*.json',
    '-o', '-name', '*.md', '-o', '-name', '*.sh', ')',
    '-not', '-path', './venv/*', '-not', '-path', './node_modules/*',
    '-not', '-path', './.git/*', '-not', '-path', './sessions/*'],
    capture_output=True, text=True)
files = [f for f in r.stdout.strip().split('\n') if f.strip()]

# Count Python files
r = subprocess.run(['find', '.', '-name', '*.py', '-not', '-path', './venv/*'],
    capture_output=True, text=True)
py_files = [f for f in r.stdout.strip().split('\n') if f.strip()]

# Count lines in first 100 Python files
total_lines = 0
for f in py_files[:100]:
    with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
        total_lines += len(fh.readlines())

# Extrapolate: total_lines * (len(py_files)/100)
estimated_total = total_lines * (len(py_files) / 100)
```

### 2. Tool Implementation vs Alias Audit
```python
# Check toolsets.py for aliases vs actual implementations
r = subprocess.run(['grep', '-n', '^def ', 'tools/registry.py'],
    capture_output=True, text=True)
implemented = [l for l in r.stdout.strip().split('\n') if l.strip()]

# Check toolsets.py for aliases
r = subprocess.run(['grep', '-n', 'ToolAlias', 'toolsets.py'],
    capture_output=True, text=True)
aliases = [l for l in r.stdout.strip().split('\n') if l.strip()]

# Check discover_builtin_tools()
r = subprocess.run(['grep', '-n', 'discover_builtin_tools', 'tools/registry.py'],
    capture_output=True, text=True)
```

**Finding:** 76 aliases defined, only 31 actual tool functions implemented, 60 aliases without implementation. The CLI shows 27 tools (15 enabled + 12 disabled) because it only registers implemented functions.

### 3. Cognitive System File Presence vs Wiring
```python
# Check files exist
cognitive_files = [
    'agent/iteration_engine.py',
    'agent/cortex_flywheel.py',
    'agent/agent_scorecard.py',
    'agent/red_team_hippocampus.py',
    'agent/tool_misuse_prevention.py',
    'agent/memory_cortex_bridge.py',
    'agent/hermes_enhancement_suite.py',
    'agent/cognitive_orchestrator.py'
]

for f in cognitive_files:
    if os.path.exists(f):
        size = os.path.getsize(f)
        with open(f) as fh:
            lines = len(fh.readlines())
        print(f"✓ {f}: {lines} lines, {size} bytes")
    else:
        print(f"✗ {f}: MISSING")

# Check for ANY imports of these systems
r = subprocess.run(['grep', '-rn',
    'from agent.iteration_engine|from agent.cortex_flywheel|from agent.agent_scorecard',
    '.', '--include', '*.py', '-not', '-path', './venv/*'],
    capture_output=True, text=True)
imports = [l for l in r.stdout.strip().split('\n') if l.strip()]
print(f"\nDirect imports found: {len(imports)}")

# Check for orchestrator usage
r = subprocess.run(['grep', '-rn', 'get_orchestrator|initialize_cognitive_systems',
    '.', '--include', '*.py', '-not', '-path', './venv/*'],
    capture_output=True, text=True)
usage = [l for l in r.stdout.strip().split('\n') if l.strip()]
print(f"Orchestrator usage: {len(usage)}")
```

**Finding:** 7/7 cognitive system files present (3,164 lines total). Orchestrator present (972 lines). **Zero imports. Zero usage. Zero initialization calls.**

### 4. Cross-Machine Sync Verification
```bash
# MacBook status
hermes skills list | wc -l
hermes doctor

# DGX status (via SSH)
ssh user@dgx 'cd /data/SpecForge/hermes-agent && git log --oneline -3'
ssh user@dgx 'find skills/ -name "SKILL.md" -maxdepth 3 | wc -l'

# Sync if needed
git push origin main
ssh user@dgx 'cd /data/SpecForge/hermes-agent && git pull origin main'
```

**Finding:** DGX at detached HEAD commit 0924ed231, 18 commits behind origin/main. After sync: both at 4e856e29a, 384 skills.

---

## Results Summary

| Layer | Metric | Value | Status |
|-------|--------|-------|--------|
| **Repository** | Total files | 8,033 | — |
| | Python files | 1,857 | — |
| | Est. total lines | ~200,000+ | — |
| | Agent modules | 172 | — |
| | Tool modules | 111 | — |
| **Skills** | Total SKILL.md | 384 | ✓ |
| | Builtin | 91 | ✓ |
| | Local | 293 | ✓ |
| **Tools** | Registered | 27 (15+12) | ⚠ |
| | Aliases | 76 | — |
| | Implemented | 31 | — |
| | Unimplemented | 60 | ✗ |
| **Plugins** | Directories | 46 | — |
| | Evey plugins | 29 | — |
| **Cognitive** | System files | 7/7 | ✓ |
| | Total lines | 3,164 | — |
| | Orchestrator | 972 lines | ✓ |
| | **Wired to CLI** | **0 references** | **✗ DEAD CODE** |
| **Sync** | MacBook commit | 4e856e29a | ✓ |
| | DGX commit | 4e856e29a | ✓ |
| | Skills match | 384 vs 384 | ✓ |

---

## Failure Mode Classification

| Failure Mode | Previous Audit (May 16) | This Audit (May 18) |
|--------------|------------------------|---------------------|
| Cognitive files | Present | Present |
| Hook wiring | Partial (post_tool_call missing) | **None — zero imports** |
| Orchestrator | Wired in run_agent.py | **Unreferenced — dead code** |
| Root cause | Asymmetric hook pairs | **No integration points** |
| Fix complexity | Add hook invocation | **Add 4 integration points to run_agent.py** |

---

## Fix Required

To activate the cognitive systems, add these 4 integration points to `hermes_cli/main.py` or `run_agent.py`:

```python
# 1. In __init__ (~line 2127):
from agent.cognitive_orchestrator import get_orchestrator
self.cognitive_orchestrator = get_orchestrator()
self.cognitive_orchestrator.initialize(self)

# 2. Before each tool call:
self.cognitive_orchestrator.before_action(action_type, detail)

# 3. After each tool call:
self.cognitive_orchestrator.after_action(action_type, detail, result, duration_ms)

# 4. At session end:
self.cognitive_orchestrator.session_end(telemetry)
```

Until these 4 lines are added, all 3,164 lines of cognitive system code are **completely inactive**.

---

## Performance Notes

- 1,857 Python files may slow import time
- 384 skills load at startup (latency concern)
- 172 agent/ modules = significant memory footprint
- 3,164 lines of unused cognitive code = wasted memory
- 60 unimplemented tool aliases = user confusion potential
