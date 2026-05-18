---
name: hermes-plugin-subprocess-scripts
version: 1.0
created: 2026-04-04
description: Architecture pattern for Hermes plugins that need to run Python code via subprocess. Use external script files in a scripts/ directory instead of inline f-string code blocks. Required when using venv-only deps (matplotlib, librosa, trimesh, PIL) or any code containing dict/set literals.
tags: [hermes, plugin, subprocess, python, architecture]
---

# Hermes Plugin Subprocess Script Pattern

## Problem
When building Hermes plugins that need to execute Python code requiring venv-only dependencies (matplotlib, librosa, trimesh, PIL, openpyxl, etc.), you cannot use inline code in f-string triple-quoted blocks. Python 3.8 (the system Python on macOS) chokes on dict literals `{}`, set literals, and any braces inside f-strings. Even Python 3.11 f-strings with complex inline code are fragile and unmaintainable.

## Solution: External Script Files

Use a `scripts/` directory inside your plugin and call them via subprocess.

### Directory Structure
```
~/.hermes/plugins/my-plugin/
  __init__.py          # Main plugin logic, format detection, orchestration
  scripts/             # One file per operation
    analyze_audio.py
    render_chart.py
    extract_data.py
```

### Core Pattern

In `__init__.py`:
```python
SCRIPTS_DIR = Path(__file__).parent / "scripts"
VENV_PYTHON = "/Users/dannygomez/hermes-agent/venv/bin/python3"

def _run_script(name: str, *args, timeout: int = 60):
    """Run a named script from scripts/ with the venv Python."""
    script = SCRIPTS_DIR / name
    result = subprocess.run(
        [VENV_PYTHON, str(script)] + [str(a) for a in args],
        capture_output=True, text=True, timeout=timeout
    )
    return result.returncode, result.stdout, result.stderr
```

Each script in `scripts/`:
```python
#!/usr/bin/env python3
"""Brief description of what this script does."""
import sys
import json

input_path = sys.argv[1]
output_path = sys.argv[2]

# ... do work ...
print(json.dumps(result))  # Always output JSON for easy parsing
```

### When to Use This Pattern

1. Any matplotlib/visualization code (requires venv + Agg backend)
2. Scientific libraries (librosa, trimesh, soundfile, openpyxl)
3. Code with dict/set literals (can't go in f-strings on Python 3.8)
4. Code blocks > 20 lines (external files are cleaner and debuggable standalone)
5. Code that might fail (you get clean stderr from subprocess)

### When NOT to Use

- Simple operations (file copy, rename, basic text) -- do inline
- Operations needing shared state with plugin -- use function calls
- One-liners with no dependency issues -- inline is fine

### Testing Scripts Standalone

Always test scripts independently before wiring into the plugin:
```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 ~/.hermes/plugins/my-plugin/scripts/analyze_audio.py /path/to/input.wav /path/to/output.png
```

### Propagation to Squad Profiles

```bash
for profile in soma-coder soma-researcher soma-tester; do
    mkdir -p ~/.hermes-profiles/$profile/plugins/my-plugin/scripts
    cp -r ~/.hermes/plugins/my-plugin/__init__.py ~/.hermes-profiles/$profile/plugins/my-plugin/
    cp -r ~/.hermes/plugins/my-plugin/scripts/*.py ~/.hermes-profiles/$profile/plugins/my-plugin/scripts/
done
```

## Pitfalls

1. NEVER use f-strings with triple quotes for subprocess code. Python 3.8 can't handle braces inside f-strings.
2. Always use VENV_PYTHON (`/Users/dannygomez/hermes-agent/venv/bin/python3`), not `python3` (system Python 3.8).
3. Scripts communicate via sys.argv (input) and stdout (output). Use JSON for structured data.
4. Timeout subprocess calls. matplotlib and librosa can hang on corrupt files. Default 60s.
5. Check exit_code before parsing stdout. Scripts may fail with import errors if deps missing from venv.

## Venv Dependency Check

```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -c "import matplotlib; print('OK')"
# If missing:
/Users/dannygomez/hermes-agent/venv/bin/python3 -m pip install matplotlib
```
