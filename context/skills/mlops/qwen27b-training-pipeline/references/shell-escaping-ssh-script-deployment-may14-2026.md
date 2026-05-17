# Shell Escaping Pitfall — SSH Script Deployment (May 14, 2026)

## Problem

When creating Python scripts on remote hosts via SSH/terminal, inline heredocs and f-strings with newlines cause unterminated string literal errors. The shell interprets `\n` and quote characters.

## Failed Attempts (5+ before finding working solution)

1. **Heredoc through SSH:** `ssh host "cat > file.py << 'EOF'...EOF"` — shell on local machine interprets the heredoc, not the remote
2. **Python one-liner with newlines:** `ssh host "python3 -c 'print(\"hello\nworld\")'"` — `\n` interpreted by local shell
3. **execute_code with triple-quoted strings:** `code="""..."""` containing `\n` — shell interprets newlines
4. **f-strings with newlines through SSH:** Shell escapes `\n` to literal newline, breaking Python syntax
5. **Base64 encoding via execute_code:** The base64 string itself gets mangled by shell escaping layers

## Working Solution: Hex Encoding

```python
import binascii
import subprocess

# 1. Read script locally
with open('/tmp/train_script.py', 'r') as f:
    content = f.read()

# 2. Encode as hex (alphabet: 0-9, a-f — zero shell metacharacters)
encoded = content.encode('utf-8').hex()

# 3. Build remote command
remote_path = '/data/SpecForge/custom_dflash/train_script.py'
remote_cmd = f"import binascii; data = binascii.unhexlify('{encoded}'); open('{remote_path}', 'w').write(data.decode('utf-8'))"

# 4. Execute via SSH
result = subprocess.run(
    ['ssh', 'djg6228@10.0.0.171', 'python3', '-c', remote_cmd],
    capture_output=True, text=True
)
```

## Alternative: Local Write + SCP

```bash
# On local machine
write_file /tmp/train_script.py "...script content..."
scp /tmp/train_script.py djg6228@10.0.0.171:/data/SpecForge/custom_dflash/
```

## Alternative: Base64 Pipe (for simple scripts)

```bash
# Encode locally and pipe through SSH
base64 -w0 < /tmp/script.py | ssh djg6228@10.0.0.171 "base64 -d > /data/remote/script.py"
```

## When Each Method Works

| Method | Complexity | Reliability | Best For |
|--------|-----------|-------------|----------|
| Hex encoding | Medium | 100% | Complex scripts, multiple shell layers |
| Local write + scp | Low | 99% | When scp is available |
| Base64 pipe | Low | 95% | Simple scripts, direct SSH |
| Heredoc | Low | 0% | Never works through SSH |
| Python one-liner | Medium | 10% | Only single-line scripts |

## Key Rule

**NEVER use heredocs through SSH or execute_code with triple-quoted strings containing newlines.**

After 5+ failed attempts across multiple sessions, hex encoding was the only reliable method for deploying multi-line Python scripts to DGX via SSH when the deployment command itself goes through shell escaping (execute_code → subprocess → ssh → remote shell).
