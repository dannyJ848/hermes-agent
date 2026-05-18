# Hermes Core Patching Guide

Session: 2026-05-09, Enhancement Cycle 7-8
Context: User explicitly corrected agent for building standalone scripts instead of patching Hermes core.

## The Correction

User: "well no you need to build this all INTO hermes code. take control."
User: "wait what? you can edit files and code and then just ask me to restart."
User: "no I mean everything you just built, you didn't build it INTO the hermes code?"

Lesson: Building tools in `~/subconscious/` is prototyping. The user considers work unfinished until it patches the actual Hermes source and requires a restart to activate.

## Finding Hermes Source Code

```bash
# Method 1: pip location
pip3 show hermes-agent | grep Location

# Method 2: which hermes → resolve symlink
which hermes
ls -la $(which hermes)  # check if symlink
readlink -f $(which hermes)  # resolve chain

# Method 3: find entry points
find /Users/dannygomez/hermes-agent -name "*.py" | grep -v venv | grep -v __pycache__ | grep -E "(main|cli|entry|agent|run)"
```

## Patching Pattern

### 1. Locate the Agent Loop

Look for files containing:
- `def run_agent(` or `def main(`
- `pre_llm_call`, `pre_tool_call`, `post_tool_call` hooks
- The main message processing loop

### 2. Insert Integration

```python
# At top of file or in __init__
import sys
sys.path.insert(0, str(Path.home() / "subconscious"))

from hermes_self_manager import full_handoff
from hermes_context_gauge import check_context_pressure

# In the agent loop, before each turn or LLM call:
pressure = check_context_pressure()
if pressure['action'] == 'CHECKPOINT_NOW':
    # Trigger full handoff
    label = full_handoff()
    # Or notify user to restart
```

### 3. Test Without Restart

```bash
python3 -c "
import sys
sys.path.insert(0, '/Users/dannygomez/subconscious')
from hermes_self_manager import detect_compression_count
print('Compressions:', detect_compression_count())
"
```

### 4. Ask for Restart

"I've patched Hermes core at `<path>`. Please restart Hermes to activate the integration."

## Common Hook Points

| Hook | File Pattern | Use Case |
|------|-------------|----------|
| `pre_llm_call` | `*hooks*.py`, `*plugin*.py` | Inject context, check pressure |
| `post_tool_call` | `*hooks*.py`, `*plugin*.py` | Log tool use, update state |
| `on_session_start` | `*session*.py`, `*cli*.py` | Resume detection, handoff check |
| `on_session_end` | `*session*.py`, `*cli*.py` | Checkpoint, distill, handoff |
| Main loop | `agent.py`, `run.py`, `main.py` | Compression monitoring |

## Pitfalls

- **venv isolation**: Hermes runs in its own venv. Your `~/subconscious/` modules may not be in `sys.path`. Add `sys.path.insert` or install as editable package.
- **Import failures on restart**: If your module has syntax errors, Hermes may fail to start. Test with `python3 -m py_compile <file>` first.
- **Version conflicts**: Hermes updates may overwrite your patches. Document patches in `~/.hermes/knowledge/` for re-application.
- **Permission**: May need `chmod` or sudo for system-wide installs. Prefer user install (`pip install --user`).

## Verification After Restart

```bash
# Check that your module loads
hermes -c "from hermes_self_manager import full_handoff; print('OK')"

# Check that hook fires
# (trigger condition manually or wait for natural occurrence)
```
