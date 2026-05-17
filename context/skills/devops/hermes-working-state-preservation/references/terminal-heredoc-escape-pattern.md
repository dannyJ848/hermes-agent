# Terminal Heredoc Escape Pattern

## Date: 2026-05-16

## Problem

Writing multi-line Python scripts via `cat << 'EOF'` in Hermes terminal tool repeatedly fails with:
```
eval: line N: unexpected EOF while looking for matching `"'
eval: line N: syntax error: unexpected end of file
```

This happens because Hermes' terminal tool passes commands through `eval`-like processing that mangles quotes, backticks, and `$` variables in heredocs.

## The Rule

**NEVER use heredocs with special characters in the terminal tool.**

Special characters that break heredocs:
- Double quotes (`"`) inside heredoc body
- Backticks (`` ` ``) — interpreted as command substitution
- `$` — interpreted as variable expansion
- Backslashes in escape sequences
- Single quotes inside single-quoted heredoc delimiter

## Working Pattern: write_file + execute

```python
# Step 1: Write script to file using write_file tool
write_file(
    path="/tmp/script.py",
    content="""#!/usr/bin/env python3
import os
print(f"Home: {os.path.expanduser('~')}")
"""
)

# Step 2: Execute via terminal
terminal("python3 /tmp/script.py")
```

## Anti-Pattern (BROKEN)

```bash
# In terminal tool — this WILL fail
cat > /tmp/script.py << 'EOF'
import os
print(f"Home: {os.path.expanduser('~')}")
EOF
# → eval: line 2: unexpected EOF while looking for matching `"'
```

## Why write_file Works

- `write_file` writes bytes directly to filesystem, no shell interpretation
- `terminal` then runs `python3 /path/to/file` — simple command, no heredoc
- No quote escaping, no variable expansion, no backtick substitution

## Session Evidence

This session had 5+ heredoc failures before switching to write_file:
- `eval: line 2: unexpected EOF while looking for matching '`
- `eval: line 153: syntax error near unexpected token`
- Host key verification failures from mangled scp commands

All resolved by writing files first, then executing.

## Related

- `safe-file-write` skill — Hermes built-in skill for file writing
- `yantrikdb-integration` skill — Uses this pattern for batch ingest scripts
