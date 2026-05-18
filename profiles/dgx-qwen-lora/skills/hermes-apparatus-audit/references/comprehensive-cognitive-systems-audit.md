# Comprehensive Cognitive Systems Audit (July 2026)

**Purpose:** Complete line-by-line wiring and functionality verification of all Hermes cognitive systems after integration.

**When to use:** After bulk integration of cognitive modules, when user asks "complete audit", or when verifying "functional wiring" (not just file presence).

---

## The 8-Phase Audit

### Phase 0: Infrastructure Verification
Verify Python environment, imports, and paths are correct.

```python
import sys, os
os.chdir('/Users/dannygomez/hermes-agent')
sys.path.insert(0, '/Users/dannygomez/hermes-agent')
venv_site = '/Users/dannygomez/hermes-agent/venv/lib/python3.11/site-packages'
if venv_site not in sys.path:
    sys.path.insert(0, venv_site)

# Verify core imports
from hermes_cli.plugins import PluginManager
from agent.cognitive_systems_plugin import _load_system
print("✅ Infrastructure ready")
```

### Phase 1: Agent Module Import Audit
Check all 160+ agent modules import cleanly and have exports.

```python
import importlib
from pathlib import Path

agent_dir = Path('/Users/dannygomez/hermes-agent/agent')
py_files = sorted([f for f in agent_dir.glob('*.py') if f.name != '__init__.py'])

results = {'ok': 0, 'import_error': 0, 'runtime_error': 0, 'no_exports': 0}
for f in py_files:
    module_name = f'agent.{f.stem}'
    try:
        mod = importlib.import_module(module_name)
        exports = [n for n in dir(mod) if not n.startswith('_') and callable(getattr(mod, n, None))]
        if exports:
            results['ok'] += 1
        else:
            results['no_exports'] += 1
    except ImportError as e:
        results['import_error'] += 1
        print(f"❌ {f.stem}: {e}")
    except Exception as e:
        results['runtime_error'] += 1
        print(f"❌ {f.stem}: RUNTIME {e}")

print(f"\nAGENT MODULES: {len(py_files)} total | {results['ok']} OK | {results['import_error']} import errors | {results['runtime_error']} runtime | {results['no_exports']} no exports")
```

**Target:** 100% import cleanly. Fix import errors immediately.

### Phase 2: Tool Module Audit
Verify all tools in `tools/` directory import and have handlers.

```python
tools_dir = Path('/Users/dannygomez/hermes-agent/tools')
py_files = sorted([f for f in tools_dir.glob('*.py') if f.name not in ('__init__.py', 'registry.py', 'tool_schemas.py')])

for f in py_files:
    module_name = f'tools.{f.stem}'
    try:
        mod = importlib.import_module(module_name)
        handlers = [n for n in dir(mod) if not n.startswith('_') and callable(getattr(mod, n))]
        print(f"✅ {f.stem}: {len(handlers)} handlers")
    except Exception as e:
        print(f"❌ {f.stem}: {e}")
```

### Phase 3: run_agent.py Hook Invocation Audit
**CRITICAL:** Verify all 6 hooks are actually invoked in the runtime.

```python
content = open('/Users/dannygomez/hermes-agent/run_agent.py').read()

hooks_to_check = [
    'on_session_start',
    'pre_llm_call', 
    'pre_tool_call',
    'post_tool_call',
    'post_llm_call',
    'on_session_end'
]

for hook in hooks_to_check:
    matches = list(re.finditer(rf'invoke_hook\(\s*"{hook}"', content))
    if matches:
        for m in matches:
            line = content[:m.start()].count('\n') + 1
            print(f"✅ {hook}: line {line}")
    else:
        print(f"❌ {hook}: NOT INVOKED — DEAD HOOK")
```

**Target:** All 6 hooks have at least one invoke_hook call in run_agent.py or model_tools.py.

### Phase 4: Cognitive Systems Functional Check
Verify all 7 cognitive systems load AND their primary functions work.

```python
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
        
        # Test primary function
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
        elif name == 'memory_cortex_bridge':
            print(f"✅ {name}: pressure={system.is_pressure()}")
        elif name == 'hermes_enhancement_suite':
            status = system.get_status()
            print(f"✅ {name}: installed={status['installed']}")
        else:
            print(f"✅ {name}: loaded")
    except Exception as e:
        print(f"❌ {name}: {e}")
```

### Phase 5: Database Integrity Audit
Check cerebrum_memory.db and cortex DB health.

```python
import sqlite3
from pathlib import Path

# Cerebrum Memory DB
cerebrum_db = Path.home() / '.hermes' / 'cerebrum_memory.db'
if cerebrum_db.exists():
    conn = sqlite3.connect(str(cerebrum_db))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables: {len(tables)}")
    for t in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {t}')
        count = cursor.fetchone()[0]
        print(f"  {t}: {count} rows")
    conn.close()

# Cortex DB
from agent.cortex_access import CortexDB
cortex = CortexDB()
stats = cortex.get_stats()
print(f"Cortex: {stats['total_nodes']} nodes, {stats['total_tips']} tips, {stats['total_edges']} edges")
```

### Phase 6: Vision Tools Audit
Verify screen capture, GUI click, GUI type tools have valid schemas.

```python
from agent.vision_tools import screen_capture_tool, gui_click_tool, gui_type_tool
from agent.vision_tools import SCREEN_CAPTURE_SCHEMA, GUI_CLICK_SCHEMA, GUI_TYPE_SCHEMA

for name, schema in [('screen_capture', SCREEN_CAPTURE_SCHEMA), ('gui_click', GUI_CLICK_SCHEMA), ('gui_type', GUI_TYPE_SCHEMA)]:
    try:
        json.dumps(schema)
        print(f"✅ {name}: valid schema")
    except Exception as e:
        print(f"❌ {name}: invalid schema - {e}")
```

### Phase 7: X Tools Audit
Verify X/Twitter tools are registered and callable.

```python
from tools.x_tool import x_search, x_tweet_fetch, x_user_tweets
for name, handler in [('x_search', x_search), ('x_tweet_fetch', x_tweet_fetch), ('x_user_tweets', x_user_tweets)]:
    print(f"✅ {name}: {handler}")
```

### Phase 8: Live Hook Firing Test
**THE GOLD STANDARD.** Actually fire all hooks and verify callbacks execute.

```python
from hermes_cli.plugins import PluginManager

pm = PluginManager()
pm.discover_and_load()

hook_fired = {}

# Wrap callbacks to track firing
for hook_name, callbacks in pm._hooks.items():
    for i, cb in enumerate(callbacks):
        if hasattr(cb, '__name__') and '_handler' in cb.__name__:
            original = cb
            def make_wrapped(orig, name):
                def wrapped(*args, **kwargs):
                    hook_fired[name] = hook_fired.get(name, 0) + 1
                    return orig(*args, **kwargs)
                return wrapped
            callbacks[i] = make_wrapped(cb, hook_name)

# Fire all hooks
pm.invoke_hook('on_session_start', session_id='audit-test', model='test', platform='cli')
pm.invoke_hook('pre_llm_call', user_message='test', conversation_history=[])
pm.invoke_hook('pre_tool_call', tool_name='terminal', args={'command': 'echo test'})
pm.invoke_hook('post_tool_call', tool_name='terminal', result='test', error='', duration_ms=100)
pm.invoke_hook('post_llm_call', assistant_response='test', conversation_history=[])
pm.invoke_hook('on_session_end', session_id='audit-test', duration_ms=1000, actions=[], errors=[])

# Verify
for h in ['on_session_start', 'pre_llm_call', 'pre_tool_call', 'post_tool_call', 'post_llm_call', 'on_session_end']:
    count = hook_fired.get(h, 0)
    status = '✅' if count > 0 else '❌'
    print(f"{status} {h}: fired {count} time(s)")
```

**Pass criteria:** Every hook fires at least once.

---

## Expected Results

| Component | Count | Status |
|-----------|-------|--------|
| Agent modules | 165 | 163 OK, 1 fixed, 1 schema-only |
| Tool modules | 83 | 83 OK |
| Cognitive systems | 7 | 7 operational |
| Plugin hooks | 6 | 6 registered & firing |
| Vision tools | 3 | 3 registered, valid schemas |
| X tools | 3 | 3 registered & callable |
| Cerebrum DB | 117 experiences, 11 tables | Healthy |
| Cortex DB | 1129 nodes, 1038 tips, 385 edges | Healthy |

---

## Key Fixes from July 2026 Audit

1. **Import path fix:** `agent/cognitive_infrastructure_hooks.py` line 20 had broken import `from cognitive_infrastructure_v2` → fixed to `from agent.cognitive_infrastructure_v2`

2. **Hook wiring verified:** All 6 hooks confirmed at:
   - `on_session_start`: run_agent.py line ~11458
   - `pre_llm_call`: run_agent.py line ~11592
   - `pre_tool_call`: model_tools.py line ~725
   - `post_tool_call`: model_tools.py line ~774
   - `post_llm_call`: run_agent.py line ~14870
   - `on_session_end`: run_agent.py line ~14984

3. **No external dependencies:** All cognitive systems in `~/hermes-agent/agent/` and `tools/`. Zero standalone scripts in `~/subconscious/` being used.

---

## Verification Commands

```bash
# Quick plugin check
hermes plugins list | grep cognitive-systems

# Quick tool check
hermes tools list | grep -E "screen_capture|gui_click|gui_type|x_"

# Database check
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM experiences"

# Full audit (run from hermes-agent directory)
source venv/bin/activate && python3 -c "
# Paste all 8 phases here
"
```
