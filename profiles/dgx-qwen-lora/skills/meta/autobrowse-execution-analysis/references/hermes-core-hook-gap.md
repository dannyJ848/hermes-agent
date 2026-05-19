# Hermes Core Hook Gap — Technical Reference

## Problem

The Hermes agent core (`hermes-agent/hermes_cli/main.py`) never calls `invoke_hook("post_tool_call", ...)` after tool execution. The hook infrastructure exists and works:

- `plugins.py:1130` — `PluginManager.invoke_hook()` is implemented
- `plugins.py:1238` — `invoke_hook()` module function exists
- `plugins.py:1299` — `invoke_hook("pre_tool_call", ...)` IS called
- `distillation/__init__.py:6926` — `register()` calls `ctx.register_hook("post_tool_call", _on_post_tool_call)`

But `invoke_hook("post_tool_call", ...)` is never called from the agent loop.

## Impact

- Autobrowse tracer captures zero real tool calls
- Analyzer detects zero patterns
- Synthesizer generates zero tips
- Graduator tracks zero applications
- The entire R191 pipeline is dead in production

## Where the Hook Should Be Called

In `hermes-agent/hermes_cli/main.py`, after tool execution completes:

```python
# After tool execution, before returning result to LLM
hook_results = invoke_hook(
    "post_tool_call",
    tool_name=tool_name,
    args=args,
    result=result,
    status="success" if success else "error",
    error=error_message if not success else "",
    duration_ms=duration_ms,
)
```

## Verification

```bash
# Check if post_tool_call is ever invoked in main.py
grep -n "invoke_hook.*post_tool_call" hermes-agent/hermes_cli/main.py
# Result: empty — confirms the gap

# Check pre_tool_call IS invoked
grep -n "invoke_hook.*pre_tool_call" hermes-agent/hermes_cli/plugins.py
# Result: L1299 — confirms pre_tool_call works
```

## Workarounds

### Option 1: Standalone Cron Tracer
Run autobrowse modules in a cron job that polls SQLite logs:
```python
# ~/subconscious/autobrowse_cron.py
import sys, time
sys.path.insert(0, '/Users/dannygomez/subconscious')
from autobrowse_tracer import get_instance as get_tracer
from autobrowse_analyzer import get_instance as get_analyzer
from autobrowse_synthesizer import get_instance as get_synth

t = get_tracer('cron')
a = get_analyzer('cron')
s = get_synth('cron')

# Poll for new tool calls from SQLite
# ... implementation depends on where tool calls are logged
```

### Option 2: Patch Hermes Core
Add to `hermes-agent/hermes_cli/main.py` after tool execution:
```python
from plugins import invoke_hook
invoke_hook("post_tool_call", tool_name=tool_name, args=args, 
            result=result, status=status, error=error)
```

### Option 3: Direct Module Testing
Test the pipeline without relying on hooks:
```python
import sys; sys.path.insert(0, '/Users/dannygomez/subconscious')
from autobrowse_tracer import get_instance as get_tracer
from autobrowse_analyzer import get_instance as get_analyzer
from autobrowse_synthesizer import get_instance as get_synth

t = get_tracer('test')
a = get_analyzer('test')
s = get_synth('test')

# Manually record calls
for i in range(25):
    t.record_call(tool_name='terminal', model_used='kimi-for-coding',
                  input_data={}, output_data={}, 
                  execution_time_ms=150.0, status='success')

# Manually analyze
traces = t.get_recent_traces(20)
patterns = a.analyze_traces(traces)
if patterns:
    tips = s.generate_tips(patterns)
    print(f"Generated {len(tips)} tips")
```

## Related Files

- `~/.hermes/plugins/distillation/__init__.py` — R191 autobrowse wiring
- `~/subconscious/autobrowse_*.py` — 4 autobrowse modules
- `hermes-agent/hermes_cli/plugins.py` — Hook infrastructure
- `hermes-agent/hermes_cli/main.py` — Agent loop (missing post_tool_call invocation)
