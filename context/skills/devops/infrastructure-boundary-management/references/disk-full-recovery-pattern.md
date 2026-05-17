# Disk Full Recovery Pattern

## Session: May 12, 2026

**Context:** MacBook Pro disk filled to 100% (898GB/926GB used). Hermes `write_file` and `terminal` tools both failed with "No space left on device" because internal temp files couldn't be created.

**What was using space:**
| Path | Size | What |
|------|------|------|
| `~/datasets` | 337GB | ML training datasets (should be on external SSD) |
| `~/Library` | 147GB | App caches, Xcode simulators |
| `~/Downloads` | 105GB | Downloads |
| `~/.ollama` | 29GB | Ollama models |
| `~/.claude-worktrees` | 13GB | Claude Code worktrees |

**User action:** Deleted 112GB Qwen scope download from `~/Downloads` to free space.

**Workaround used while disk was full:**
Instead of `write_file` locally + `scp` (which fails), write scripts directly on the remote DGX via SSH:

```bash
# Create script on remote host where disk is available
ssh djg6228@10.0.0.171 "printf '%s\n' '#!/bin/bash' 'cd /data/SpecForge/custom_dflash' 'source eval_venv/bin/activate' 'lm_eval --tasks bbh ... > /tmp/lm_eval_bbh.log 2>&1 &' 'echo \$!' > /tmp/start_bbh.sh"

# Execute on remote
ssh djg6228@10.0.0.171 "bash /tmp/start_bbh.sh > /tmp/bbh.pid; cat /tmp/bbh.pid"
```

**Key insight:** The `printf '%s\n'` approach avoids heredoc issues and works reliably for creating multi-line scripts via SSH.

**Prevention:** Move large datasets to external storage BEFORE disk fills. The DGX has `/mnt/bigssd` (7.3TB) specifically for this purpose.
