# Shell Escaping: SSH Script Transfer (May 14, 2026)

## Problem

When creating Python scripts via SSH/terminal, inline heredocs and f-strings with newlines cause `unterminated string literal` errors. The shell interprets `\n` and quote characters.

**Failed approaches:**
- Triple-quoted strings through `execute_code`
- Inline heredocs (`cat << 'EOF'`)
- Escaped newlines in f-strings

All fail because the shell layer interprets special characters before Python sees them.

## Working Solution: Base64 Encoding

Encode the script as base64 locally, pipe through SSH, decode on remote.

```bash
# Encode locally and transfer
echo '#!/usr/bin/env python3
import sys
print("Hello from remote")
' | base64 | ssh djg6228@10.0.0.171 "base64 -d > /tmp/script.py && chmod +x /tmp/script.py"

# Or from a file
base64 /path/to/script.py | ssh djg6228@10.0.0.171 "base64 -d > /tmp/script.py"
```

**Python equivalent (for execute_code):**
```python
import base64
import subprocess

script = '''#!/usr/bin/env python3
import sqlite3
# ... complex script with newlines and quotes ...
'''

encoded = base64.b64encode(script.encode()).decode()
cmd = f'echo "{encoded}" | ssh djg6228@10.0.0.171 "base64 -d > /tmp/script.py"'
subprocess.run(cmd, shell=True)
```

## Why This Works

- Base64 is shell-safe (only A-Z, a-z, 0-9, +, /, =)
- No quote interpretation, no newline handling
- Works for any script complexity (JSON, XML, Python with nested quotes)

## When to Use

- Transferring scripts to remote hosts via SSH
- Writing multi-line files through `execute_code` tool
- Any content with quotes, newlines, or special characters

## NEVER Use

- Heredocs through SSH: `ssh host "cat << 'EOF' ... EOF"` → fails
- Triple-quoted strings in `execute_code` with newlines → shell interprets `\n`
- Inline Python with f-strings containing newlines → unterminated string literal
