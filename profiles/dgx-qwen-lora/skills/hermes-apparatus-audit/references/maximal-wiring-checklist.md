# Maximal Wiring Verification Checklist

Complete 12-layer audit to verify every cognitive system is not just present but actually wired into the Hermes agent loop.

**Core principle:** Integration (files in right place) ≠ Wiring (connected to hooks). Both must be verified.

---

## Layer 1: Iteration Engine / Cognitive Loop

```python
import os
from pathlib import Path

hermes_dir = Path.home() / "hermes-agent"
run_agent = hermes_dir / "run_agent.py"
content = run_agent.read_text()

checks = {
    "pre_action hooks": "pre_action" in content,
    "post_action hooks": "post_action" in content,
    "iteration_engine instantiated": "iteration_engine" in content,
    "subconscious_plugin_loader called": "subconscious_plugin_loader" in content,
    "cortex_flywheel integrated": "cortex_flywheel" in content,
    "cognitive_infrastructure_hooks": "cognitive_infrastructure_hooks" in content,
    "brain_to_toolintel": "brain_to_toolintel" in content,
    "agent_scorecard": "agent_scorecard" in content,
    "tool_misuse_prevention": "tool_misuse_prevention" in content,
    "red_team_hippocampus": "red_team_hippocampus" in content,
    "memory_cortex_bridge": "memory_cortex_bridge" in content,
    "hermes_enhancement_suite": "hermes_enhancement_suite" in content,
}

for check, found in checks.items():
    print(f"{'✅' if found else '❌'} {check}")
```

**Pass criteria:** iteration_engine + at least 6 of 10 cognitive modules referenced in run_agent.py.

---

## Layer 2: Autobrowse / Vision / Screen Capture

```python
vision_modules = [
    "agent/autobrowse_engine.py",
    "agent/vision_loop.py",
    "agent/screen_capture.py",
    "agent/gui_automation.py",
    "agent/visual_grounding.py",
    "agent/eyes.py",
    "agent/vision_analyzer.py",
    "agent/perception.py",
]

for mod in vision_modules:
    exists = (hermes_dir / mod).exists()
    print(f"{'✅' if exists else '❌'} {mod}")
```

**Also verify:**
- `which playwright` — Playwright CLI installed
- `which cliclick` — macOS GUI automation
- `which screencapture` — macOS screen capture

---

## Layer 3: Skills System

```bash
# Count skills
ls ~/.hermes/skills/*/SKILL.md | wc -l

# Verify skill loading works
python3 -c "from hermes_cli.skills import list_skills; print(len(list_skills()))"
```

---

## Layer 4: Tool Registry & Custom Tools

```python
tools_dir = hermes_dir / "tools"
custom_tools_dir = Path.home() / ".hermes" / "tools"

builtin = len(list(tools_dir.glob("*.py"))) if tools_dir.exists() else 0
custom = len(list(custom_tools_dir.glob("*.py"))) if custom_tools_dir.exists() else 0

print(f"Built-in tools: {builtin}")
print(f"Custom tools: {custom}")

# Verify registry
from tools.registry import registry
print(f"Registered tools: {len(registry._tools)}")
```

---

## Layer 5: Plugin System

```python
plugins_dir = Path.home() / ".hermes" / "plugins"
if plugins_dir.exists():
    plugin_dirs = [d for d in plugins_dir.iterdir() if d.is_dir() and not d.name.startswith("__")]
    registered = 0
    for pd in plugin_dirs:
        init = pd / "__init__.py"
        if init.exists() and "register" in init.read_text().lower():
            registered += 1
    print(f"Plugins: {len(plugin_dirs)}, Registered: {registered}")
```

---

## Layer 6: Databases & Storage

```python
import sqlite3

db_files = [
    ("unified_context.db", Path.home() / ".hermes" / "unified_context.db"),
    ("cerebrum_memory.db", Path.home() / ".hermes" / "cerebrum_memory.db"),
    ("tool_capability.db", Path.home() / ".hermes" / "tool_capability.db"),
    ("skill_rewards.db", Path.home() / ".hermes" / "skill_rewards.db"),
    ("cortex.db", Path.home() / ".hermes" / "cortex.db"),
]

for name, path in db_files:
    if path.exists():
        size = path.stat().st_size
        try:
            conn = sqlite3.connect(str(path))
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            rows = sum(conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0] for t in tables)
            conn.close()
            status = "✅" if rows > 0 else "⚠️ EMPTY"
            print(f"{status} {name}: {size} bytes, {len(tables)} tables, {rows} rows")
        except Exception as e:
            print(f"❌ {name}: CORRUPTED ({e})")
    else:
        print(f"❌ {name}: MISSING")
```

---

## Layer 7: Memory Systems

```python
memory_modules = [
    "agent/memory_cortex_bridge.py",
    "agent/cerebrum_memory.py",
    "agent/episodic_memory.py",
    "agent/semantic_memory.py",
    "agent/procedural_memory.py",
    "agent/memory_consolidation.py",
    "agent/distillation_engine.py",
    "agent/tip_injection.py",
]

for mod in memory_modules:
    exists = (hermes_dir / mod).exists()
    print(f"{'✅' if exists else '❌'} {mod}")
```

---

## Layer 8: Knowledge Base

```python
knowledge_dir = Path.home() / ".hermes" / "knowledge"
if knowledge_dir.exists():
    files = list(knowledge_dir.glob("*.md"))
    print(f"Knowledge files: {len(files)}")
```

---

## Layer 9: Configuration

```python
config = Path.home() / ".hermes" / "config.yaml"
if config.exists():
    content = config.read_text()
    checks = ["tools", "plugins", "memory", "skills", "cron", "gateway"]
    for c in checks:
        print(f"{'✅' if c in content else '❌'} {c} configured")
```

---

## Layer 10: Cron & Scheduling

```bash
ls ~/.hermes/cron/ | wc -l
# Should show active cron jobs
```

---

## Layer 11: Gateway / Telegram

```python
gateway_modules = [
    "gateway/telegram_bot.py",
    "gateway/message_router.py",
    "gateway/hooks.py",
    "gateway/webhook_handler.py",
]

for mod in gateway_modules:
    exists = (hermes_dir / mod).exists()
    print(f"{'✅' if exists else '❌'} {mod}")
```

---

## Layer 12: Self-Evolution / Training Gym

```python
evolution_modules = [
    "agent/training_gym.py",
    "agent/elo_tournament.py",
    "agent/tip_evolution.py",
    "agent/skill_evolution.py",
    "agent/auto_distillation.py",
    "agent/self_evaluation_loop.py",
    "agent/reflection_engine.py",
    "agent/hindsight_engine.py",
]

for mod in evolution_modules:
    exists = (hermes_dir / mod).exists()
    print(f"{'✅' if exists else '❌'} {mod}")
```

---

## External Directory Check

```python
standalone_dirs = ["~/subconscious", "~/atropos", "~/training_gym", "~/cortex"]
for d in standalone_dirs:
    exists = os.path.exists(os.path.expanduser(d))
    print(f"{'⚠️ EXISTS' if exists else '✅ GONE'} {d}")
```

**Target:** All cognitive systems in `agent/` or `tools/`. Zero external standalone directories.

---

## Hook Wiring Deep Check

```python
import re

# What hooks does run_agent.py invoke?
content = run_agent.read_text()
invoked = set(re.findall(r'invoke_hook\(\s*"(\w+)"', content))
print(f"Hooks invoked by run_agent.py: {invoked}")

# What do cognitive modules register?
cognitive_systems = [
    "cognitive_infrastructure_hooks.py",
    "cortex_flywheel.py",
    "brain_to_toolintel.py",
    "agent_scorecard.py",
    "tool_misuse_prevention.py",
    "red_team_hippocampus.py",
    "memory_cortex_bridge.py",
    "hermes_enhancement_suite.py",
]

for system in cognitive_systems:
    path = hermes_dir / "agent" / system
    if path.exists():
        mod_content = path.read_text()
        hooks = set(re.findall(r'"(\w+)"', mod_content))
        hook_names = [h for h in hooks if any(x in h for x in ['pre_', 'post_', 'on_', 'transform_'])]
        if hook_names:
            print(f"✅ {system}: registers {hook_names}")
        else:
            print(f"❌ {system}: ORPHANED — no hook registration")
```

**Critical finding from May 2026 audit:** All cognitive modules existed in `agent/` but NONE registered hooks. They were all orphaned — present but not functional.
