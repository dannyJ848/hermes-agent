# SSH Python Script Transfer Patterns (May 15, 2026)

## The Problem

Transferring multi-line Python scripts to a remote host via SSH is fraught with shell interpolation traps. Quotes, braces, `$` variables, and backticks all get interpreted by the local shell before reaching the remote host.

**Symptoms of corruption:**
- `SyntaxError: unexpected EOF while parsing` — quotes got mangled
- `NameError: name 'true' is not defined` — `True` became `true`
- Script runs but produces wrong results — braces `{}` stripped, `$` variables expanded
- `KeyError` on dict literals — quotes around keys disappeared

**Root causes:**
1. Double quotes inside heredoc interpreted by outer shell
2. `$variable` expanded by local shell before reaching remote
3. Backticks `` ` `` executed by local shell
4. Curly braces `{}` trigger shell brace expansion
5. The `execute_code` tool adds its own escaping layer, creating double-escaping

## Pattern 1: Single-Quoted Heredoc Delimiter (Simplest)

Use `<< 'DELIMITER'` (single-quoted) to prevent ALL shell interpolation:

```bash
ssh host "cat > /tmp/script.py << 'PYEOF'
import requests
import json

url = 'http://localhost:8000/v1/completions'
payload = {
    'model': '/data/models/Qwen3.6-27B-Uncensored',
    'prompt': 'Write about AI.',
    'max_tokens': 512,
    'temperature': 0.7
}

resp = requests.post(url, json=payload)
print(f'Tokens: {resp.json()[\"usage\"][\"completion_tokens\"]}')
PYEOF"
```

**Why it works:** The single quotes around `PYEOF` tell the shell to treat everything between `<< 'PYEOF'` and `PYEOF` as literal text. No interpolation, no expansion.

**Limitation:** Does not work inside `execute_code` tool (which has its own string escaping). Use Pattern 2 or 3 for `execute_code`.

## Pattern 2: Base64 Encoding (Most Reliable)

Encode the script as base64 locally, pipe through SSH, decode on remote:

```bash
# From local file
base64 /path/to/script.py | ssh host "base64 -d > /tmp/script.py"

# From inline string
echo '#!/usr/bin/env python3
import requests
# ... complex script ...
' | base64 | ssh host "base64 -d > /tmp/script.py && python3 /tmp/script.py"
```

**Python equivalent (for execute_code tool):**
```python
import base64
import subprocess

script = '''#!/usr/bin/env python3
import requests
url = 'http://localhost:8000/v1/completions'
resp = requests.post(url, json={"model": "test", "prompt": "hello", "max_tokens": 10})
print(resp.json())
'''

encoded = base64.b64encode(script.encode()).decode()
cmd = f'echo "{encoded}" | ssh djg6228@spark "base64 -d > /tmp/script.py && python3 /tmp/script.py"'
subprocess.run(cmd, shell=True)
```

**Why it works:** Base64 alphabet is shell-safe (A-Z, a-z, 0-9, +, /, =). No character in base64 triggers shell interpolation.

## Pattern 3: scp/rsync Transfer (Best for Complex Scripts)

Write locally, transfer via scp, execute remotely:

```bash
# Write locally (no shell interpolation concerns)
cat > /tmp/benchmark.py << 'EOF'
import time
import requests

url = 'http://localhost:8000/v1/completions'
payload = {
    'model': '/data/models/Qwen3.6-27B-Uncensored',
    'prompt': 'Write a comprehensive essay about artificial intelligence.',
    'max_tokens': 512,
    'temperature': 0.7
}

speeds = []
for i in range(3):
    start = time.time()
    resp = requests.post(url, json=payload)
    elapsed = time.time() - start
    data = resp.json()
    gen_tokens = data['usage']['completion_tokens']
    speed = gen_tokens / elapsed
    speeds.append(speed)
    print(f'Run {i+1}: {gen_tokens} tokens in {elapsed:.1f}s = {speed:.1f} tok/s')

avg = sum(speeds) / len(speeds)
print(f'Average: {avg:.1f} tok/s')
EOF

# Transfer and execute
scp /tmp/benchmark.py djg6228@spark:/tmp/
ssh djg6228@spark "python3 /tmp/benchmark.py"
```

**Why it works:** The local shell only sees the `cat` and `scp` commands, not the script content. The script content is written to a local file without shell interpretation, then transferred as binary data.

## Pattern 4: Python One-Liner with JSON Payload (For Simple Scripts)

For very simple scripts (single API call, no loops), use Python `-c` with JSON string:

```bash
ssh host "python3 -c \"import requests; print(requests.post('http://localhost:8000/v1/completions', json={'model': 'test', 'prompt': 'hello', 'max_tokens': 10}).json())\""
```

**Limitation:** Breaks on nested quotes, loops, or multi-line logic. Use Patterns 1-3 for anything non-trivial.

## Anti-Patterns (What NOT to Do)

### Anti-Pattern 1: Double-Quoted Heredoc
```bash
# WRONG — shell interpolates $variables and backticks
ssh host "cat > /tmp/script.py << EOF
import os
print(os.environ.get('HOME'))  # $HOME expanded by LOCAL shell
EOF"
```

### Anti-Pattern 2: Inline Python with Double Escaping
```bash
# WRONG — execute_code tool escapes once, shell escapes again
ssh host "python3 -c \"import json; print(json.dumps({'key': 'value'}))\""
# Often becomes: python3 -c "import json; print(json.dumps({key: value}))"
# Quotes around 'key' and 'value' disappear
```

### Anti-Pattern 3: JSON Inside Python Inside Shell
```bash
# WRONG — triple nesting of quote types is fragile
ssh host "python3 -c \"import requests; requests.post('http://host/api', json={\\\"key\\\": \\\"value\\\"})\""
# The \\\" often collapses to \" or " unpredictably
```

### Anti-Pattern 4: Heredoc Inside execute_code
```python
# WRONG — execute_code's string literal handling + shell heredoc = double trouble
code = """
ssh host "cat > /tmp/script.py << 'EOF'
# ... script ...
EOF"
"""
# The inner 'EOF' may get mangled by execute_code's parser
```

## Decision Tree

| Situation | Recommended Pattern |
|-----------|---------------------|
| Simple script, terminal tool directly | Pattern 1: Single-quoted heredoc |
| Complex script, execute_code tool | Pattern 2: Base64 encoding |
| Script >20 lines, any tool | Pattern 3: scp transfer |
| One API call, no loops | Pattern 4: Python one-liner |
| Script with JSON payloads | Pattern 2 or 3 (never 1 or 4) |
| Script with f-strings | Pattern 2 or 3 |
| Script with regex patterns | Pattern 2 or 3 |

## Verification

After transferring, ALWAYS verify the script was not corrupted:

```bash
# Check for syntax errors
ssh host "python3 -m py_compile /tmp/script.py"

# Check file content (spot-check key lines)
ssh host "grep -n 'max_tokens' /tmp/script.py"

# Check for common corruption signatures
ssh host "grep -c 'true' /tmp/script.py"  # Should be 0 (Python uses True, not true)
ssh host "grep -c '\\\\$' /tmp/script.py"  # Should match expected $var count
```

## Real-World Example: vLLM Benchmark Script

This script was corrupted 3 times before finding the right pattern:

```python
# CORRECT — Pattern 3 (scp) for complex benchmark
import subprocess

script = '''import time
import requests

url = 'http://localhost:8000/v1/completions'
payload = {
    'model': '/data/models/Qwen3.6-27B-Uncensored',
    'prompt': 'Write a comprehensive essay about artificial intelligence.',
    'max_tokens': 512,
    'temperature': 0.7
}

# Warmup
requests.post(url, json=payload)
time.sleep(2)

speeds = []
for i in range(3):
    start = time.time()
    resp = requests.post(url, json=payload)
    elapsed = time.time() - start
    data = resp.json()
    gen_tokens = data['usage']['completion_tokens']
    speed = gen_tokens / elapsed
    speeds.append(speed)
    print(f'Run {i+1}: {gen_tokens} tokens in {elapsed:.1f}s = {speed:.1f} tok/s')

avg = sum(speeds) / len(speeds)
print(f'Average: {avg:.1f} tok/s')
'''

# Write locally
with open('/tmp/bench_vllm.py', 'w') as f:
    f.write(script)

# Transfer and run
subprocess.run(['scp', '/tmp/bench_vllm.py', 'djg6228@spark:/tmp/'])
subprocess.run(['ssh', 'djg6228@spark', 'python3', '/tmp/bench_vllm.py'])
```

## Related References

- `references/shell-escaping-ssh-script-transfer.md` — Base64 encoding pattern (Pattern 2)
- `references/shell-escaping-ssh-script-transfer-extended.md` — execute_code tool guardrails and recovery strategies
