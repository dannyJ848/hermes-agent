# Live Functional Verification (May 2026)

**Purpose:** Go beyond file-existence checks. Actually fire hooks and verify cognitive systems produce real output.

**When to use:** After any integration, upgrade, or when user asks "is everything actually working."

---

## Layer 13: Live Hook Firing Verification

File presence and import checks are necessary but NOT sufficient. The gold standard is firing each hook and verifying callbacks execute. This catches silent failures where hooks are registered but callbacks throw exceptions.

```python
from hermes_cli.plugins import PluginManager

pm = PluginManager()
pm.discover_and_load()

# Track which callbacks actually fire
hook_fired = {}

# Wrap all callbacks to detect execution
for hook_name, callbacks in pm._hooks.items():
    for i, cb in enumerate(callbacks):
        original = cb
        def make_tracker(orig, name):
            def tracked(*args, **kwargs):
                hook_fired[name] = hook_fired.get(name, 0) + 1
                return orig(*args, **kwargs)
            return tracked
        callbacks[i] = make_tracker(cb, hook_name)

# Fire every hook with realistic arguments
pm.invoke_hook('on_session_start', session_id='audit-test', model='test', platform='cli')
pm.invoke_hook('pre_llm_call', user_message='test', conversation_history=[])
pm.invoke_hook('pre_tool_call', tool_name='terminal', args={'command': 'echo test'})
pm.invoke_hook('post_tool_call', tool_name='terminal', result='test', error='', duration_ms=100)
pm.invoke_hook('post_llm_call', assistant_response='test', conversation_history=[])
pm.invoke_hook('on_session_end', session_id='audit-test', duration_ms=1000, actions=[], errors=[])

# Verify all fired
for h in ['on_session_start', 'pre_llm_call', 'pre_tool_call', 'post_tool_call', 'post_llm_call', 'on_session_end']:
    count = hook_fired.get(h, 0)
    status = '✅' if count > 0 else '❌'
    print(f"{status} {h}: fired {count} time(s)")
```

**Pass criteria:** Every hook fires at least once with no exceptions.

---

## Layer 14: Cognitive System Functional Deep Check

Import checks verify syntax. Functional checks verify the module actually WORKS — databases connect, methods return sensible data, state is consistent.

```python
from agent.cognitive_systems_plugin import _load_system

systems = [
    'iteration_engine', 'cortex_flywheel', 'agent_scorecard',
    'tool_misuse_prevention', 'red_team_hippocampus',
    'memory_cortex_bridge', 'hermes_enhancement_suite',
]

for name in systems:
    try:
        system = _load_system(name)
        if system is None:
            print(f"❌ {name}: _load_system returned None")
            continue
            
        # Test the system's primary function
        if name == 'iteration_engine':
            ctx = system.before_action('terminal', 'ls -la')
            system.after_action('terminal', 'test', 'success', '', 100)
            stats = system.get_learning_stats()
            print(f"✅ {name}: {stats['total_experiences']} experiences")
            
        elif name == 'cortex_flywheel':
            stats = system.get_stats()
            print(f"✅ {name}: {stats['total_nodes']} nodes")
            
        elif name == 'agent_scorecard':
            stats = system.compute_scorecard()
            print(f"✅ {name}: score={stats['overall_score']}")
            
        elif name == 'tool_misuse_prevention':
            result = system.validate_tool_call('terminal')
            print(f"✅ {name}: validate={result[0]}")
            
        elif name == 'red_team_hippocampus':
            status = system.get_status()
            print(f"✅ {name}: attacks={status['total_attacks']}")
            
        elif name == 'memory_cortex_bridge':
            pressure = system.is_pressure()
            print(f"✅ {name}: pressure={pressure}")
            
        elif name == 'hermes_enhancement_suite':
            status = system.get_status()
            print(f"✅ {name}: installed={status['installed']}")
            
    except Exception as e:
        print(f"❌ {name}: {e}")
```

**Pass criteria:** All 7 systems load AND their primary functions execute without error.

---

## Layer 15: Database Column & Schema Integrity

Empty tables with wrong schemas are silent failures. Verify actual column names match expected structure.

```python
import sqlite3
from pathlib import Path

cerebrum_db = Path.home() / '.hermes' / 'cerebrum_memory.db'
conn = sqlite3.connect(str(cerebrum_db))
cursor = conn.cursor()

# Verify experiences table has all expected columns
cursor.execute('PRAGMA table_info(experiences)')
actual_cols = {c[1] for c in cursor.fetchall()}
expected_cols = {'id', 'action_hash', 'action_type', 'action_detail', 'result', 
                 'error_pattern', 'lesson', 'approach', 'frequency', 'speed_ms'}
missing = expected_cols - actual_cols
if missing:
    print(f"❌ experiences table missing columns: {missing}")
else:
    print(f"✅ experiences table schema correct")

# Check for data anomalies
cursor.execute('SELECT result, COUNT(*) FROM experiences GROUP BY result')
results = cursor.fetchall()
for result, count in results:
    print(f"  {result}: {count}")

conn.close()
```

**Pass criteria:** All expected columns present. Data distribution looks reasonable (not 100% one result type).

---

## Layer 16: Tool Module Import & Handler Audit

Every tool module must import cleanly and have callable handlers.

```python
import importlib
from pathlib import Path

tools_dir = Path('/Users/dannygomez/hermes-agent/tools')
py_files = sorted([f for f in tools_dir.glob('*.py') if f.name not in ('__init__.py', 'registry.py', 'tool_schemas.py')])

for f in py_files:
    module_name = f'tools.{f.stem}'
    try:
        mod = importlib.import_module(module_name)
        handlers = [name for name in dir(mod) 
                   if not name.startswith('_') and callable(getattr(mod, name))]
        print(f"✅ {f.stem}: {len(handlers)} handlers")
    except Exception as e:
        print(f"❌ {f.stem}: {e}")
```

**Pass criteria:** 100% of tool modules import cleanly. Each has at least 1 callable handler.

---

## Layer 17: Agent Module Import & Export Audit

Every agent module must import cleanly and expose callable exports.

```python
import importlib
from pathlib import Path

agent_dir = Path('/Users/dannygomez/hermes-agent/agent')
py_files = sorted([f for f in agent_dir.glob('*.py') if f.name != '__init__.py'])

for f in py_files:
    module_name = f'agent.{f.stem}'
    try:
        mod = importlib.import_module(module_name)
        exports = [name for name in dir(mod) 
                   if not name.startswith('_') and callable(getattr(mod, name))]
        if exports:
            print(f"✅ {f.stem}: {len(exports)} exports")
        else:
            print(f"⚠️ {f.stem}: no exports (schema-only?)")
    except ImportError as e:
        print(f"❌ {f.stem}: IMPORT ERROR — {e}")
    except Exception as e:
        print(f"❌ {f.stem}: RUNTIME ERROR — {e}")
```

**Pass criteria:** 100% import cleanly. Investigate any with zero exports (may be schema-only, which is fine if documented).

---

## Complete Audit Command

Run all phases in sequence:

```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
$(cat << 'PYEOF'
# Paste all verification blocks above here
# ...
PYEOF
)"
```

**Expected runtime:** ~3 seconds for full audit.
**Expected output:** All ✅ with counts for databases, nodes, experiences, etc.
