# SSH Remote File Deployment Patterns

## Problem

When deploying files or running Python scripts on remote hosts via SSH, nested quotes in heredocs and command substitution frequently cause `SyntaxError: unterminated string literal` or similar failures.

## Anti-Patterns (Don't Do This)

### Heredoc with Nested Quotes via SSH

```python
# BROKEN: nested quotes cause SyntaxError
r = subprocess.run(['ssh', 'user@host', 
                   'cat > /tmp/test.py << "EOF"\nprint("hello")\nEOF\npython3 /tmp/test.py'],
                  capture_output=True, text=True)
```

**Why it fails**: The shell on the remote host interprets the quote nesting differently than expected. `"` inside `<<` heredoc delimiters conflicts with the Python string's `"` delimiters.

### Triple-Nested f-Strings via SSH

```python
# BROKEN: triple nesting breaks
r = subprocess.run(['ssh', 'user@host', 
                   f'python3 -c "print({value})"'],
                  capture_output=True, text=True)
```

**Why it fails**: The f-string interpolation happens in Python, then the result goes through SSH shell interpretation, then through the remote `python3 -c` argument parsing. Each layer has different escaping rules.

## Proven Patterns (Do This Instead)

### Pattern 1: Write Local, SCP, Execute Remote

Best for: Python scripts, config files, any file with quotes/special chars.

```python
import subprocess
import tempfile
import os

# Step 1: Write locally
script_content = '''import sys
print("Hello with quotes: 'nested'")
value = 42
print(f"The value is {value}")
'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(script_content)
    local_path = f.name

# Step 2: Copy to remote
try:
    r = subprocess.run(['scp', local_path, 'user@host:/tmp/script.py'],
                      capture_output=True, text=True, check=True)
    
    # Step 3: Execute remotely
    r = subprocess.run(['ssh', 'user@host', 'python3 /tmp/script.py'],
                      capture_output=True, text=True, check=True)
    print(r.stdout)
finally:
    os.unlink(local_path)
```

**Advantages**:
- No quote nesting issues (file written to disk, read by remote Python)
- Works with any complexity of Python code
- Can use `check=True` for proper error handling

### Pattern 2: Base64 Encode for Inline Transfer

Best for: Small files when you can't use SCP.

```python
import base64
import subprocess

content = '''print("Hello with quotes")
'''
encoded = base64.b64encode(content.encode()).decode()

# Single SSH command: decode and execute
r = subprocess.run(['ssh', 'user@host', 
                   f'echo "{encoded}" | base64 -d | python3'],
                  capture_output=True, text=True)
```

**Advantages**:
- Single SSH round-trip
- No quote issues (base64 is quote-safe)
- Works through bastion hosts where SCP is blocked

**Limitations**:
- Content size limited by max command line length (~128KB typical)
- Binary content may have issues

### Pattern 3: Simple Commands Only

Best for: Simple commands with no quotes or special chars.

```python
# OK: simple command, no quotes
r = subprocess.run(['ssh', 'user@host', 'ls -la /tmp'],
                  capture_output=True, text=True)

# OK: single-quoted string, no nesting
r = subprocess.run(['ssh', 'user@host', 'echo hello world'],
                  capture_output=True, text=True)

# DANGEROUS: nested quotes
r = subprocess.run(['ssh', 'user@host', 'echo "hello world"'],
                  capture_output=True, text=True)
```

### Pattern 4: Use SSH with Explicit Shell Escape

Best for: When you must pass complex arguments.

```python
import shlex

command = 'python3 -c "print(\\"hello\\")"'
escaped = shlex.quote(command)

r = subprocess.run(['ssh', 'user@host', command],
                  capture_output=True, text=True)
```

**Note**: `shlex.quote()` handles the local shell escaping, but the remote shell still interprets the command. Use only when necessary.

## Decision Tree

```
Need to run Python on remote?
├── Can use SCP? → Pattern 1 (write local, SCP, execute)
│   └── Most reliable, always preferred
├── SCP blocked? → Pattern 2 (base64 encode)
│   └── Good for small scripts (< 100KB)
└── Just simple commands? → Pattern 3 (simple commands)
    └── Never use quotes or special chars
```

## Session Evidence

**Date**: 2026-05-18
**Context**: Porting Hermes Agent to DGX via SSH
**Failure**: `SyntaxError: unterminated string literal` when trying to use heredoc with nested quotes in SSH subprocess call.
**Resolution**: Switched to Pattern 1 (write local, SCP, execute) — worked immediately.

## Related

- `safe-file-write` skill: for local file write workarounds
- `hermes-working-state-deployment` skill: for DGX deployment procedures
