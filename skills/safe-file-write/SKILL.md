---
name: safe-file-write
description: Workaround for write_file truncation and heredoc special-char issues. Use when writing files with thinking tags, backslashes, unicode, or very large content.
trigger: When write_file fails with heredoc/special-char errors, when content contains thinking tags, or when writing files >5KB
---

# Safe File Write Workaround

## Problem
1. `write_file` uses heredoc internally — breaks on special chars like thinking tags, backslashes, unicode
2. Long responses get truncated at token ceiling mid-tool-call, leaving broken arguments
3. `execute_code` missing `import os` causes NameError

## Solutions

### Method 1: execute_code with import (RELIABLE — 93% success)
```python
import os
from hermes_tools import write_file

content = "your content here"  # Python string, no heredoc issues
result = write_file(
    path=os.path.expanduser("~/path/to/file"),
    content=content
)
```

### Method 2: Base64 via terminal (for content with thinking tags)
```python
import base64, os
from hermes_tools import terminal

content = "content with liuspecial tags"
b64 = base64.b64encode(content.encode()).decode()
path = os.path.expanduser("~/path/to/file")
result = terminal(f'echo "{b64}" | base64 -d > "{path}"')
```

### Method 3: Chunked writes (for very large files >10KB)
```python
import os
from hermes_tools import write_file, patch

# Write first chunk
write_file(path=os.path.expanduser("~/path/to/file"), content=first_chunk)

# Append subsequent chunks using patch (replace last line with continuation)
# OR use execute_code to append:
import os
from hermes_tools import terminal
terminal(f'cat >> "{os.path.expanduser("~/path/to/file")}" << '"'"'HERMES_EOF'"'"'
additional content here
HERMES_EOF')
```

**Warning (2026-04-21):** The `terminal()` tool can produce false-positive "Foreground command uses '&' backgrounding" errors when using heredocs with markdown content containing `>` or `|` characters, even when no actual `&` is present. If this occurs, fall back to Method 4 or 5 (Python-based writes) instead of heredocs.

**CRITICAL (May 16, 2026):** The `&` character in shell scripts triggers Hermes' backgrounding detector even when it's inside a string literal or heredoc. This affects:
- HTML entities: `&amp;`, `&lt;`, `&gt;`
- URL query parameters: `?key=value&other=thing`
- Bash `&&` operators
- Any content with ampersands

**When this happens:** The terminal tool rejects with "Foreground command uses '&' backgrounding. Use terminal(background=true)..."

**Fix:** Immediately switch to `write_file` tool instead of terminal heredocs. The `write_file` tool does not use shell execution and is not affected by the `&` detector. Do NOT try to escape or work around the terminal tool — it's faster to use write_file.

**Rule of thumb:** For any file containing `&`, `<`, `>`, `$`, backticks, or newlines — use `write_file` directly, not terminal heredocs.

### Method 4: Python write via terminal (bypasses all issues)
```python
from hermes_tools import terminal
import json, os

content = "your content"
path = os.path.expanduser("~/path/to/file")
# Escape for shell using json.dumps
escaped = json.dumps(content)
result = terminal(f'python3 -c "import os; os.makedirs(os.path.dirname(\"{path}\") or \".\", exist_ok=True); open(\"{path}\", \"w\").write({escaped})"')
```

### Method 5: pathlib one-liner via terminal (SIMPLEST — for "No such file or directory" failures)
When `write_file` fails with "No such file or directory" even though the directory exists
(common on macOS with `~/` paths in wiki/knowledge dirs), use this pattern:

**Root cause:** Never hardcode `/home/user/` or `/root/` — the actual home directory may differ
(e.g. `/Users/dannygomez/` on macOS, `/home/ubuntu/` on Linux, `/root/` in containers but not on host).
`write_file`'s internal shell redirect fails on non-existent absolute paths. Always use `~` or
`os.path.expanduser('~')`.

**Additional root cause (discovered 2026-04-21):** `write_file`'s internal shell may expand `~` to the WRONG
home directory entirely (e.g. `/home/ubuntu` instead of `/Users/dannygomez` on macOS). Even passing `~/wiki/...`
to write_file can fail because the tool's shell context differs from the user's actual home. The Python pathlib
approach below bypasses this entirely by resolving the path from inside the correct Python process.
```python
from hermes_tools import terminal

content = "your content here"
path_rel = "wiki/concepts/filename.md"  # relative to home
r = terminal(f'python3 -c "import pathlib; pathlib.Path.home().joinpath(\'{path_rel}\').write_text({repr(content)})"')
# Check success:
if r["exit_code"] == 0: print("Written successfully")
```
This bypasses write_file's internal heredoc/shell path resolution entirely.

### Method 6: SSH Base64 Transfer (for remote file deployment — May 14, 2026)
When deploying files to remote hosts via SSH, standard heredocs and Python string literals fail because the shell interprets newlines and quotes. Base64 encoding the entire file content locally and decoding on the remote is the most reliable pattern.

**Problem:**
```bash
# This fails — shell mangles newlines in the Python code
ssh host "python3 -c 'print(\"hello\nworld\")'"
```

**Solution — Full file transfer via base64:**
```python
import base64
import subprocess

# 1. Read file locally
with open('/tmp/script.py', 'rb') as f:
    content = f.read()

# 2. Encode as base64
encoded = base64.b64encode(content).decode()

# 3. Transfer to remote and decode
remote_path = '/data/remote/script.py'
write_cmd = f"import base64; data = base64.b64decode('{encoded}'); open('{remote_path}', 'wb').write(data)"

result = subprocess.run(
    ['ssh', 'user@host', 'python3', '-c', write_cmd],
    capture_output=True, text=True
)
```

**One-liner variant (terminal tool):**
```bash
# Encode locally and pipe through SSH
base64 -w0 < /tmp/script.py | ssh user@host "base64 -d > /data/remote/script.py && chmod +x /data/remote/script.py"
```

**Why this works:**
- Base64 alphabet (A-Z, a-z, 0-9, +, /, =) contains no shell metacharacters
- Newlines in original content are preserved in the base64 encoding
- No heredoc, no quote escaping, no `\n` interpretation issues
- Works for binary files too (images, compiled objects)

**When to use:**
- Deploying Python scripts to remote servers via SSH
- Transferring files when `scp` is not available or fails
- Any content containing newlines, quotes, backslashes, or unicode
- Binary file deployment

**Anti-pattern: Using execute_code with multi-line strings for SSH**
- Wrong: `execute_code` with `code="""..."""` then SSH via subprocess — the code string itself gets mangled
- Right: `write_file` locally → base64 encode → SSH decode
- Right: `terminal` with base64 pipe one-liner

### Method 7: Hex Encoding for SSH Python Script Deployment (May 14, 2026)

When deploying multi-line Python scripts to remote hosts via SSH, even base64 can fail if the SSH command itself is constructed via `execute_code` or `terminal` with shell escaping. The most reliable pattern is hex encoding:

```python
import binascii
import subprocess

# 1. Read script locally
with open('/tmp/script.py', 'r') as f:
    content = f.read()

# 2. Encode as hex (no shell metacharacters at all)
encoded = content.encode('utf-8').hex()

# 3. Build remote command — hex string is shell-safe
remote_path = '/data/remote/script.py'
remote_cmd = f"import binascii; data = binascii.unhexlify('{encoded}'); open('{remote_path}', 'w').write(data.decode('utf-8'))"

# 4. Execute via SSH
result = subprocess.run(
    ['ssh', 'user@host', 'python3', '-c', remote_cmd],
    capture_output=True, text=True
)
```

**Why hex is safer than base64 for SSH:**
- Hex alphabet (0-9, a-f) has ZERO shell metacharacters
- No `+`, `/`, or `=` that might need URL/percent encoding
- No padding characters
- Works even when the SSH command is passed through multiple shell layers

**Complete working example (verified May 14, 2026):**
```python
# Local script content
script = '''#!/usr/bin/env python3
import torch
print(f"CUDA: {torch.cuda.is_available()}")
'''

# Encode
encoded = script.encode('utf-8').hex()

# Transfer via SSH (one-liner)
import subprocess
cmd = f"python3 -c \"import binascii; open('/tmp/test.py','w').write(binascii.unhexlify('{encoded}').decode())\""
result = subprocess.run(['ssh', 'dgx', cmd], capture_output=True, text=True)
```

**CRITICAL: NEVER use heredocs through SSH or execute_code with triple-quoted strings containing newlines.**
After 5+ failed attempts with various escaping approaches, hex encoding was the only reliable method for deploying Python scripts to DGX via SSH.

### Method 7: Hex Encoding for SSH Python Script Deployment (May 14, 2026)

When deploying multi-line Python scripts to remote hosts via SSH, even base64 can fail if the SSH command itself is constructed via `execute_code` or `terminal` with shell escaping. The most reliable pattern is hex encoding:

```python
import binascii
import subprocess

# 1. Read script locally
with open('/tmp/script.py', 'r') as f:
    content = f.read()

# 2. Encode as hex (no shell metacharacters at all)
encoded = content.encode('utf-8').hex()

# 3. Build remote command — hex string is shell-safe
remote_path = '/data/remote/script.py'
remote_cmd = f"import binascii; data = binascii.unhexlify('{encoded}'); open('{remote_path}', 'w').write(data.decode('utf-8'))"

# 4. Execute via SSH
result = subprocess.run(
    ['ssh', 'user@host', 'python3', '-c', remote_cmd],
    capture_output=True, text=True
)
```

**Why hex is safer than base64 for SSH:**
- Hex alphabet (0-9, a-f) has ZERO shell metacharacters
- No `+`, `/`, or `=` that might need URL/percent encoding
- No padding characters
- Works even when the SSH command is passed through multiple shell layers

**Complete working example (verified May 14, 2026):**
```python
# Local script content
script = '''#!/usr/bin/env python3
import torch
print(f"CUDA: {torch.cuda.is_available()}")
'''

# Encode
encoded = script.encode('utf-8').hex()

# Transfer via SSH (one-liner)
import subprocess
cmd = f"python3 -c \"import binascii; open('/tmp/test.py','w').write(binascii.unhexlify('{encoded}').decode())\""
result = subprocess.run(['ssh', 'dgx', cmd], capture_output=True, text=True)
```

**CRITICAL: NEVER use heredocs through SSH or execute_code with triple-quoted strings containing newlines.**
After 5+ failed attempts with various escaping approaches, hex encoding was the only reliable method for deploying Python scripts to DGX via SSH.
1. ALWAYS `import os` at the top of execute_code blocks
2. For files >5KB, use execute_code + write_file (not raw write_file)
3. If response feels long, break into multiple smaller tool calls
4. Never use write_file directly with content containing thinking tags — always wrap in execute_code
5. Use patch() for small edits instead of rewriting entire files
6. If write_file fails with "No such file or directory" but dir exists, use Method 5 (pathlib one-liner)
7. **For files with duplicated/merged content from previous versions, use read_file first to check for corruption before patching** — patch may match the wrong instance of a repeated string, causing content duplication or deletion. When patch fails repeatedly on a complex file, rewrite the entire file cleanly via execute_code + write_file instead of fighting patch.
