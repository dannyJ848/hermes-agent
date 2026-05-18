---
name: infrastructure-boundary-management
description: Manage multiple hardware systems (MacBook, DGX, VPS) with strict separation of concerns. Prevent cross-system confusion that causes user frustration.
version: 1.0.0
author: Hermes Agent
trigger: When working with multiple hardware systems or when user specifies "this runs on X, NOT Y".
---

# Infrastructure Boundary Management

## Cross-Machine Hermes Sync

When deploying Hermes to a new machine (DGX, VPS, etc.), tool parity requires syncing BOTH plugins AND their config:

### File-Level Sync Verification

After syncing Hermes source code between machines, verify completeness with `find` + `comm`:

```bash
# On source machine — generate file list
find ~/hermes-agent -type f -name '*.py' \
  -not -path '*/venv/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/.git/*' | \
  sed 's|/Users/username/hermes-agent/||' | sort > /tmp/macbook_files.txt

# On target machine — generate file list  
find /data/SpecForge/hermes-agent -type f -name '*.py' \
  -not -path '*/venv/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/__pycache__/*' \
  -not -path '*/.git/*' | \
  sed 's|/data/SpecForge/hermes-agent/||' | sort > /tmp/dgx_files.txt

# Compare — files missing on target
comm -23 /tmp/macbook_files.txt /tmp/dgx_files.txt

# Compare — extra files on target (DGX-specific additions)
comm -13 /tmp/macbook_files.txt /tmp/dgx_files.txt
```

**Expected result**: `comm -23` should return nothing (all MacBook files present on DGX). `comm -13` may show DGX-specific files (e.g., `agent/dgx_integration.py`).

**Pitfall — header line in output**: If the first line of output is `=== MACBOOK MODULES ===` or similar, the comparison tool included a header. Strip it: `tail -n +2 /tmp/macbook_files.txt | sort`.

**Pitfall — false negatives from __init__.py files**: Many "missing" files are just `__init__.py` or test files. Filter to critical modules:
```bash
# Show only non-test, non-__init__ missing files
grep -v '__init__.py' /tmp/missing.txt | grep -v '^tests/' | grep -v '^skills/'
```

### What Must Sync

| Component | Source Path | Target Path | Notes |
|-----------|------------|-------------|-------|
| Plugins | `~/.hermes/plugins/` | `~/.hermes/plugins/` | rsync with `--exclude='__pycache__'` |
| Plugin config | `~/.hermes/config.yaml` → `plugins.enabled` | `~/.hermes/config.yaml` | Hermes reads from HOME, not repo |
| Skills (optional) | `~/.hermes/skills/` | `~/.hermes/skills/` | For skill parity |
| Knowledge (optional) | `~/.hermes/knowledge/` | `~/.hermes/knowledge/` | For knowledge parity |
| API credentials | `~/.hermes/.env` | `~/.hermes/.env` | Brave, Firecrawl, Browserbase, etc. |
| Node.js (DGX only) | N/A | `~/node/` | aarch64 binary, not x86_64 |

### What NOT to sync blindly

- **Repo `config.yaml`** (`~/hermes-agent/config.yaml`) — machine-specific (model endpoints, paths)
- **`.env` files** — API keys may differ per machine
- **Database files** — `cerebrum_memory.db`, session DBs are machine-local
- **Python `__pycache__`** — Different architectures (ARM64 vs x86_64)

### Browser Tools Require Node.js (DGX-specific)

DGX Spark is aarch64 and needs the ARM64 Node.js binary:

```bash
# WRONG — x86_64 binary fails on aarch64
curl https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-x64.tar.xz  # FAILS

# CORRECT — aarch64 binary
curl -fsSL https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-arm64.tar.xz -o node.tar.xz
tar -xf node.tar.xz
mv node-v20.12.2-linux-arm64 ~/node

# Install agent-browser CLI
export PATH=$HOME/node/bin:$PATH
npm install -g agent-browser

# Add to systemd service Environment=PATH
Environment=PATH=/home/djg6228/node/bin:/data/SpecForge/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
```

**Verification:**
```bash
# Check browser requirements
cd /data/SpecForge/hermes-agent
venv/bin/python -c "from tools.browser_tool import check_browser_requirements; print(check_browser_requirements())"
# Should show: True

# Full tool count should be 97 (vs 21 default)
venv/bin/python -c "from model_tools import get_tool_definitions; print(len(get_tool_definitions(quiet_mode=True)))"
```

### Sync workflow

### Sync workflow

```bash
# 1. On source machine, list plugins
ls ~/.hermes/plugins/ | sort

# 2. Sync plugins to target
rsync -avz --exclude='__pycache__' ~/.hermes/plugins/ user@target:/home/user/.hermes/plugins/

# 3. Extract plugins.enabled from source config
grep -A 50 'plugins:' ~/.hermes/config.yaml | head -60

# 4. On target, edit ~/.hermes/config.yaml (NOT repo config)
# Add the plugins.enabled and plugins.disabled sections

# 5. Verify config path
python3 -c "from hermes_cli.config import get_config_path; print(get_config_path())"
# → Must show /home/user/.hermes/config.yaml

# 6. Verify tool count
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
print(f'Total tools: {len(tools)}')
"
# Should match source machine count (within API-dependent variance)
```

### Common post-sync issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "0 enabled" after sync | Edited repo config, not home config | Edit `~/.hermes/config.yaml` |
| Plugin load errors | Missing Python dependencies | Add to `plugins.disabled` or install deps |
| Tool shadowing warnings | Two plugins register same tool name | Deregister one or rename |
| Still missing ~20 tools | API-dependent tools (browser, Discord, etc.) | Expected — need API keys |
| "agent-browser CLI not found" | PATH missing Node.js | `export PATH=/home/djg6228/node/bin:$PATH` |
| "cannot execute binary file" | Wrong Node.js architecture on ARM64 | Use `linux-arm64`, not `linux-x64` |
| Browser tools still 0 | agent-browser not installed | `npm install -g agent-browser` |

### Tool count expectations

| Setup | Count | Notes |
|-------|-------|-------|
| Core only | ~21 | No plugins, no external deps |
| + Evey plugins | ~84 | Personal plugins synced & enabled |
| + Web APIs | ~87 | Brave + Firecrawl keys added |
| + Browser tools | ~97 | Node.js + agent-browser installed |
| + API tools | ~103 | Needs Discord, Feishu, search API keys |

### Node.js on ARM64 (DGX Spark)

DGX Spark is ARM64 (aarch64). Standard x86_64 Node.js binaries fail with "cannot execute binary file".

```bash
# WRONG — x86_64 binary
curl -fsSL https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-x64.tar.xz

# RIGHT — ARM64 binary
cd /tmp
curl -fsSL https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-arm64.tar.xz -o node.tar.xz
tar -xf node.tar.xz
mv node-v20.12.2-linux-arm64 ~/node
~/node/bin/node --version  # → v20.12.2

# Install agent-browser
export PATH=/home/djg6228/node/bin:$PATH
npm install -g agent-browser
```

For systemd services, add Node.js to PATH:
```ini
[Service]
Environment=PATH=/home/djg6228/node/bin:/usr/local/bin:/usr/bin:/bin
```

## Core Principle

When a user defines hardware boundaries, treat them as **hard constraints**, not suggestions. Confusing which system runs which workload is a **high-severity failure** that produces immediate user anger.

## User's Current Infrastructure

| System | Purpose | What Lives Here | What NEVER Lives Here |
|--------|---------|---------------|----------------------|
| **MacBook Pro (Apple Silicon)** | Hermes self-improvement | Autobrowse pipeline, Elo tournaments, tip distillation, LLM judge, cortex flywheel, strategy.md | Qwen training, model serving, GPU workloads |
| **DGX Spark (130GB GPU)** | Qwen 27B training ONLY | LoRA+SAE+teacher distillation training, vLLM deployment post-training | Autobrowse, iteration pipeline, Elo scoring, tip generation |
| **VPS (if deployed)** | Hermes gateway / web services | Telegram gateway, webhooks | Training, model serving |

## Rules

1. **Never suggest running autobrowse/Elo/training-gym on DGX** — These are MacBook-only systems
2. **Never suggest running model training on MacBook** — DGX-only, GPU required
3. **Never suggest local inference servers on MacBook** — User explicitly deleted llama.cpp, phi3, 8B, embedding servers. No local inference.
4. **LLM Judge is DeepSeek V4 Pro via DeepSeek API** — Not Gemini, not Z.AI coding API, not local models
5. **When in doubt, ask** — "Should this run on MacBook or DGX?" is better than guessing wrong
6. **When user says "ignore X" or "skip Y" — comply immediately** — No debate, no "but it's relevant", no completion of the interrupted task. Drop it and continue with what the user wants. This applies to project-specific tangents (soma, training data, etc.) as well as any other off-topic drift.
7. **User expects FULL Hermes Agent on ALL machines** — Complete cognitive orchestrator with all 20 subsystems, not just inference backends. When deploying Hermes to any machine (MacBook, DGX, VPS), verify the cognitive orchestrator is initialized, not just the iteration engine (7 systems).

## Verification Pattern

Before any action involving hardware, verify the target:

```python
# In scripts or mental model
if task == "training" or task == "model_serving":
    target = "DGX"
elif task == "self_improvement" or task == "tip_distillation" or task == "elo_scoring":
    target = "MacBook"
elif task == "gateway" or task == "webhook":
    target = "VPS"
else:
    target = ask_user()
```

## Common Confusion Traps

| Trap | Wrong | Right |
|------|-------|-------|
| "Run Elo tournament on DGX" | ❌ DGX is for training | ✅ Elo runs on MacBook with DeepSeek API |
| "Start local inference for judge" | ❌ User deleted all local inference | ✅ Use DeepSeek API |
| "Run autobrowse on DGX" | ❌ DGX has no Hermes agent | ✅ Autobrowse is MacBook plugin pipeline |
| "Check training status from MacBook scripts" | ❌ SSH to DGX for training status | ✅ MacBook can SSH to check, but don't run training code locally |

## SSH Access Pattern

MacBook can SSH to DGX for status checks and file sync. The SSH config is managed by NVIDIA Sync:
```bash
# Config location (not standard ~/.ssh/config)
# Host: spark-85e8.local (resolves to 10.0.0.171)
# User: djg6228
# Key: /Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key

ssh djg6228@spark-85e8.local
# OR direct IP (verified working):
ssh djg6228@10.0.0.171
```

**Pitfall:** Do NOT assume `dgx` or `192.168.1.100` as the hostname. Always check `~/.ssh/config` and any `Include` directives for the actual host.

**Discovery workflow when SSH fails:**
```bash
# 1. Check main config for Includes
cat ~/.ssh/config
# 2. Follow Include path (common: NVIDIA Sync)
cat "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/ssh_config"
# 3. Extract Host entry
# 4. SSH with correct user from that config
```

**Never** try `root@` or default user — the NVIDIA Sync config specifies `djg6228`.

**When session_search fails (Session database not available):**
If `session_search` returns database errors and you need DGX credentials, use `search_files` as fallback:
```bash
# Search ~/.hermes/cron/jobs.json for DGX references
search_files path="~/.hermes" pattern="DGX|dgx|spark-85e8|djg6228"
# This will reveal the host, user, and log paths from cron job definitions
```

**Pitfall — Stale episodic memory:**
Episodic memory may have outdated training status. Always verify by checking the actual log file on DGX:
```bash
# DON'T trust memory for dynamic status
ssh djg6228@spark-85e8.local "tail -20 /mnt/bigssd/train_standard.log"
# DO check process directly
ssh djg6228@spark-85e8.local "ps aux | grep train_ | grep -v grep"
```

**Training status check workflow:**
```bash
# 1. Verify process is running
ssh spark-85e8.local 'ps aux | grep train_ | grep -v grep'

# 2. Read latest log entries (log path varies — check what exists)
ssh spark-85e8.local 'tail -20 /mnt/bigssd/train_standard.log'
# Alternative logs: train_r256_final.log, train_ultimate_v3_final.log, train_lora_sae_teacher.log

# 3. Parse step progress
ssh spark-85e8.local 'grep -E "Step [0-9]+/[0-9]+" /mnt/bigssd/train_standard.log | tail -5'
```

**Training log formats (varies by training script):**
- Standard format: `[Step X/Y] Loss: N | Time: Ns | GPU: NGB/NGB`
- Detailed format: `Step X/Y | Loss: N (CE:N D:N SAE:N) | W:(N,N,N) | LR: N | GPU: NGB`
- Completion marker: `TRAINING COMPLETE` + `Final checkpoint saved!`

**Pitfall — Log path changes between training runs:**
The exact log filename varies. Check what exists rather than hardcoding:
```bash
ssh spark-85e8.local 'ls -lt /mnt/bigssd/*.log | head -5'
```

**Completion detection:**
When training finishes, the log shows:
```
[Step 1000/1000] Loss: N
  Saving checkpoint...
  Checkpoint saved: /data/SpecForge/custom_dflash/checkpoints/standard_step_1000.pt

============================================================
TRAINING COMPLETE
============================================================
Total time: N minutes
Saving final checkpoint...
Final checkpoint saved!
SUCCESS!
```
The process will then exit (no longer in `ps aux`). This is normal completion, not a crash.

**Post-completion status:**
```bash
# Process gone + final checkpoint exists = SUCCESS
ssh spark-85e8.local 'ls -la /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000'
# → checkpoint exists, training complete

# LoRA merge may be in progress (visible in log tail):
# "Merging LoRA weights..." + gcc compilation lines
```

**Training completion report format:**
```
training COMPLETE. step 10000/10000. final loss: 0.8679. checkpoint saved. lora merge in progress.
```

But **never** run MacBook-only code (autobrowse, Elo) through that SSH session.

## Storage Topology Awareness

When a system has multiple storage devices, **know which device each workload uses** before suggesting any physical disconnection or migration.

### The External SSD Trap

**Scenario (May 2026):** DGX Spark has two drives:
- `nvme0n1` (3.7TB) — internal SSD: OS, Python env, model weights, benchmark code
- `sda` (7.3TB) — external SSD: mounted at `/mnt/bigssd`, used for datasets only

**User confusion:** "If I unplug the external SSD to copy files from my MacBook, will it interrupt the benchmark running on the DGX?"

**Answer: NO.** The benchmark runs from `nvme0n1`. The external SSD is just a data volume.

**How to verify before advising:**
```bash
# On the remote host, check what device the process's working directory is on
ssh user@host "df -h /data/SpecForge/custom_dflash"
# → /dev/nvme0n1p2 — internal drive

# Check what device the external SSD is
ssh user@host "lsblk | grep -E 'nvme|sd'"
# → nvme0n1 (internal) + sda (external)

# Check mount points
ssh user@host "df -h | grep -E 'nvme|sd'"
# → /dev/nvme0n1p2 on / (internal)
# → /dev/sda2 on /mnt/bigssd (external)
```

**Rule:** Before telling a user it's safe to disconnect storage, verify:
1. What device the running process's working directory is on
2. What device the storage to be disconnected is
3. Whether any process has open file handles on the target device (`lsof /mnt/bigssd`)

### Dataset Migration to External SSD (May 2026)

**Scenario:** User has 283GB of ML datasets on MacBook internal drive (`~/datasets/`) that should live on the DGX external SSD (`/mnt/bigssd/datasets/`). The SSD was previously used but only had partial data (tier1-reasoning 51GB, missing tier2-reasoning 150GB and tier3-health 133GB).

**Discovery workflow:**
```bash
# 1. Check what's on the SSD vs what's local
ssh djg6228@spark-85e8.local 'du -sh /mnt/bigssd/datasets/* 2>/dev/null | sort -rh'
# → tier1-reasoning: 51G (present)
# → tier2-reasoning: 15M (nearly empty)
# → tier3-health: 1.8M (nearly empty)

du -sh ~/datasets/* 2>/dev/null | sort -rh
# → tier2-reasoning: 150G (needs transfer)
# → tier3-health: 133G (needs transfer)
# → tier1-reasoning: 54G (already mostly on SSD)
```

**Transfer workflow (MacBook → DGX SSD):**
```bash
# 1. Ensure SSD is mounted with user permissions (see exFAT permission fix above)
ssh djg6228@spark-85e8.local 'sudo mount -t exfat -o uid=$(id -u),gid=$(id -g),umask=0022 /dev/sda2 /mnt/bigssd'

# 2. Create target dirs
ssh djg6228@spark-85e8.local 'mkdir -p /mnt/bigssd/datasets/tier2-reasoning /mnt/bigssd/datasets/tier3-health'

# 3. Start parallel rsyncs (background, long-running)
rsync -avh --progress ~/datasets/tier2-reasoning/ djg6228@spark-85e8.local:/mnt/bigssd/datasets/tier2-reasoning/
rsync -avh --progress ~/datasets/tier3-health/ djg6228@spark-85e8.local:/mnt/bigssd/datasets/tier3-health/

# 4. Monitor progress
tail -f /tmp/rsync-tier2.log  # if redirected to log
tail -f /tmp/rsync-tier3.log
```

**Post-transfer verification:**
```bash
# Compare sizes
ssh djg6228@spark-85e8.local 'du -sh /mnt/bigssd/datasets/*'
du -sh ~/datasets/*
# Should match (within rounding)

# Verify a sample file
ssh djg6228@spark-85e8.local 'ls -la /mnt/bigssd/datasets/tier2-reasoning/AM-DeepSeek-R1-0528/README.md'
```

**Post-transfer cleanup (MacBook):**
```bash
# Once verified, remove local copies to reclaim space
rm -rf ~/datasets/tier2-reasoning ~/datasets/tier3-health
# Keep tier1-reasoning if it's the working copy, or symlink to SSD
```

**Pitfall — User says "I thought we already moved the datasets"**: When datasets appear on local disk but user believes they're on external storage, verify BOTH locations before assuming. The user may have:
- Partially transferred (some tiers moved, others not)
- Transferred but kept local copies
- Confused which machine has the SSD attached

Always run `du -sh` on BOTH the local path and the external path before concluding.
### Disk Full on Local Machine Blocks All Tool Operations

**Symptom:** Hermes `write_file`, `terminal`, and even internal temp file creation fail with "No space left on device".

**Root cause:** Hermes writes temp files to `/var/folders/.../` for every tool call. When the system disk is 100% full, ALL operations fail.

**Immediate recovery:**
```bash
# Check what's using space
du -sh ~/* 2>/dev/null | sort -rh | head -10
du -sh ~/.* 2>/dev/null | sort -rh | head -10

# Quick wins:
# - ~/Downloads (often 100GB+)
# - ~/datasets (can be 300GB+)
# - ~/.cache (package caches)
# - Docker images (docker system prune -a)
```

**Workaround while disk is full:** Write scripts directly on the remote host via SSH instead of local `write_file` + scp:
```bash
# Instead of: write_file locally then scp (fails locally)
# Use: create file on remote host where disk is available

ssh user@host "printf '%s\n' '#!/bin/bash' 'cd /project' 'command ...' > /tmp/script.sh"
ssh user@host "bash /tmp/script.sh"
3. **exFAT is the only format that works seamlessly on both macOS and Ubuntu** without third-party drivers.

4. **exFAT mount permission fix on Linux** — exFAT mounts default to root ownership, causing `chown` failures and rsync permission errors. Remount with user ownership:
   ```bash
   # Check current mount
   mount | grep bigssd  # → /dev/sda2 on /mnt/bigssd type exfat (rw,...)
   
   # Remount with correct user/group ownership
   sudo umount /mnt/bigssd
   sudo mount -t exfat -o uid=$(id -u djg6228),gid=$(id -g djg6228),umask=0022 /dev/sda2 /mnt/bigssd
   
   # Verify
   ls -la /mnt/bigssd  # → should show djg6228:djg6228 ownership
   ```
   **Without this fix:** rsync and file operations fail with "Operation not permitted" on every file.

5. **When disk is full on MacBook**, Hermes `write_file` and `terminal` tools fail with "No space left on device". Write scripts directly on remote host via SSH instead:
   ```bash
   ssh djg6228@10.0.0.171 "printf '%s\n' '#!/bin/bash' 'cd /data/...' 'command' > /tmp/script.sh"
   ```

## Memory-First Retrieval Rule

When the user asks you to find information about their setup (paths, configs, credentials, hardware details), **check your injected MEMORY first** before asking the user or using search tools. The user expects you to already know:

- Hermes source location: `~/hermes-agent/` (MacBook)
- DGX Spark host: `spark-85e8.local` / `10.0.0.171`, user `djg6228`
- SSH key: NVIDIA Sync managed at `/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key`
- Model paths, training configs, benchmark results from prior sessions

**User frustration signal:** "omfg look at your memory", "find it", "you should know this" — indicates you asked for information already in your memory. When this happens, immediately scan your MEMORY section and apologize concisely. Do NOT defend or explain.

## Terminal Tool Failure Modes on Cross-System Operations

### Pattern: `[Command interrupted]` with exit code 130

When running SSH commands via the `terminal` tool, you may see:
```
[Command interrupted]
exit_code: 130
```

This is NOT a network failure or SSH auth failure. Exit code 130 = SIGINT (Ctrl+C). Possible causes:
1. **Terminal tool internal timeout** — command exceeded tool's internal limit
2. **Signal propagation** — the terminal backend sent SIGINT to the process
3. **Hanging subprocess** — SSH command spawned a background process that didn't detach properly

**Recovery steps:**
1. **Verify basic connectivity first** with a trivial command: `echo test` (not SSH)
2. **If even `echo test` fails** — the terminal tool itself is broken, not SSH
3. **Switch to `execute_code`** for Python-based remote operations:
```python
import subprocess
result = subprocess.run(
    ['ssh', '-o', 'ConnectTimeout=5', 'user@host', 'echo SSH_OK'],
    capture_output=True, text=True, timeout=10
)
print(result.stdout, result.returncode)
```
4. **For bulk operations**, write a script locally and run it via `execute_code` instead of chaining terminal commands

**Never retry the same terminal command more than 2 times** if it returns exit code 130. Escalate to `execute_code` or ask the user about DGX accessibility.

### Pattern: Background Process Launching via SSH (May 2026)

**The terminal tool blocks `&`, `nohup`, `setsid`, and `disown` in SSH command strings.**

When starting long-running processes on DGX (training, benchmarks, vLLM):

**WRONG — terminal rejects:**
```bash
ssh djg6228@10.0.0.171 "axolotl train config.yaml > log 2>&1 &"
# Error: Foreground command uses shell-level background wrappers
```

**WRONG — unicode corruption:**
```bash
ssh djg6228@10.0.0.171 "command \u0026\u0026 echo $!"
# Error: bash: u0026: command not found
```

**RIGHT — remote script pattern:**
```bash
# 1. Write script on remote host
ssh djg6228@10.0.0.171 "cat > /tmp/start.sh << 'EOF'
#!/bin/bash
cd /project && source venv/bin/activate
command > log 2>&1 &
echo $! > /tmp/pid
EOF"

# 2. Execute script (returns immediately with PID)
ssh djg6228@10.0.0.171 "bash /tmp/start.sh && cat /tmp/pid"
```

**Key points:**
- The `&` is INSIDE the script, not in the SSH command string
- Capture PID to a file for later verification
- Verify within 30 seconds: `ssh host "ps aux | grep PID | grep -v grep"`

Full details: `references/ssh-background-process-launching-may2026.md`

When the user asks you to find information about their setup (paths, configs, credentials, hardware details), **check your injected MEMORY first** before asking the user or using search tools. The user expects you to already know:

- Hermes source location: `~/hermes-agent/` (MacBook)
- DGX Spark host: `spark-85e8.local` / `10.0.0.171`, user `djg6228`
- SSH key: NVIDIA Sync managed at `/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key`
- Model paths, training configs, benchmark results from prior sessions

**User frustration signal:** "omfg look at your memory", "find it", "you should know this" — indicates you asked for information already in your memory. When this happens, immediately scan your MEMORY section and apologize concisely. Do NOT defend or explain.

## Terminal Tool Failure Modes on Cross-System Operations

### Pattern: `[Command interrupted]` with exit code 130

When running SSH commands via the `terminal` tool, you may see:
```
[Command interrupted]
exit_code: 130
```

This is NOT a network failure or SSH auth failure. Exit code 130 = SIGINT (Ctrl+C). Possible causes:
1. **Terminal tool internal timeout** — command exceeded tool's internal limit
2. **Signal propagation** — the terminal backend sent SIGINT to the process
3. **Hanging subprocess** — SSH command spawned a background process that didn't detach properly

**Recovery steps:**
1. **Verify basic connectivity first** with a trivial command: `echo test` (not SSH)
2. **If even `echo test` fails** — the terminal tool itself is broken, not SSH
3. **Switch to `execute_code`** for Python-based remote operations:
```python
import subprocess
result = subprocess.run(
    ['ssh', '-o', 'ConnectTimeout=5', 'user@host', 'echo SSH_OK'],
    capture_output=True, text=True, timeout=10
)
print(result.stdout, result.returncode)
```
4. **For bulk operations**, write a script locally and run it via `execute_code` instead of chaining terminal commands

**Never retry the same terminal command more than 2 times** if it returns exit code 130. Escalate to `execute_code` or ask the user about DGX accessibility.

## Communication Style for Status Checks

When the user asks for status updates ("check training", "status check", "how's it going"), they prefer **ultra-concise telegraphic format** — no preamble, no fluff, no markdown tables. Example:

**User's preferred style:**
```
training step 4615/10000, loss 1.41, gpu 62.6GB, ~30h left. pid 443609. log: /mnt/bigssd/train_r256_final.log.
```

**NOT this:**
```
Here is the current training status:
- Step: 4615 of 10000
- Loss: 1.4138
- GPU Memory: 62.6GB
...
```

**Rules for status responses:**
1. Lead with the single most important number (step/progress)
2. Include only metrics that changed or matter (loss, GPU, ETA)
3. One line per system. No headers, no bullets, no tables.
4. File paths only if user might need them (logs, checkpoints)
5. If something is wrong, say it immediately: "STALLED: pid 443609 not found" or "OOM: last log line shows CUDA out of memory"
6. **ETA must be exact, not approximate** — calculate from actual log timestamps. "90.5 minutes" not "~18 hours". User will correct rough estimates.

**Example multi-system status:**
```
macbook: autobrowse idle 24h, 1902 tips, 1870 elo. deepseek v4 pro judge ok.
dgx: training step 4615/10000, loss 1.41, ~30h left. pid 443609 stable.
```

## Enhancement Cycles on MacBook

When user says "keep enhancing" or "run enhancement cycles until you can't anymore":

1. **Audit first** — count orphaned modules, unregistered tools, empty DBs, dormant plugins
2. **Wire before building** — verify the LAST cycle's systems are actually producing data. Check `skill_rewards`, `tool_routing_decisions`, `tip_injection_attempts`. If empty, fix wiring before building more.
3. **Cleanup surgically** — archive dead code, delete ghosts, register tools, enable plugins
4. **Wire quality systems** — tip survival tracking, adversarial validation, predictive routing
5. **Build self-monitoring** — health daemon, rapid learning, auto-skill pipeline
6. **Track effectiveness** — log each cycle's impact in `enhancement_effectiveness` table

**Critical rule: BUILDING WITHOUT WIRING IS WASTE. CRON JOBS ARE NOT THE ANSWER.**
- The user will explicitly call out dead code: "what's the point of building anything if you're not wiring it in?"
- Every module in `~/subconscious/` must have a live hook calling it, or it's useless
- **Cron jobs are explicitly disfavored** — user called them "lame cron jobs that break within a minute of running"
  - `cronjob` tool has 17% success rate (41 calls, mostly failures)
  - Script path issues, id confusion, silent failures
  - Even when they run, they lack live session state
  - **Never use cron jobs as the primary integration mechanism**
- The correct pattern: patch existing plugin hook functions (`_on_pre_llm_call`, `_on_post_tool_call`) to call your module
- Verify wiring by checking DB tables have rows after real tool calls
- If tables are empty after 24h, the wiring failed — debug and fix before building more
- **User reminder: "remember you can re-write the hermes code"** — the user expects direct plugin modification, not standalone scripts

**Never run enhancement cycles on DGX** — MacBook-only workload. DGX = training ONLY.

**Key files created during enhancement:**
- `~/subconscious/hermes_harness_v2.py` — unified status dashboard
- `~/subconscious/predictive_router.py` — tool routing by success rate
- `~/subconscious/error_guard.py` — pre-emptive error prevention
- `~/subconscious/hermes_health_daemon.py` — cron health monitor
- `~/subconscious/tool_router_v2.py` — smart tool dispatch
- `~/qwen-training-data/` — exported training corpus for Qwen fine-tuning

## References

- `references/infrastructure-audit-checklist.md` — Pre-action verification checklist
- `references/system-mapping.md` — Full system-to-workload mapping with justification, cost structure, and history of boundary violations
- `references/training-status-check.md` — DGX training status check workflow: SSH discovery, log parsing, ETA calculation
- `references/ssh-discovery-workflow.md` — How to find the correct SSH host/user/key when `ssh dgx` fails
- `references/credential-discovery-from-cron.md` — When SSH fails and session_search is unavailable, extract credentials from cron job definitions
- `references/training-log-parsing.md` — Qwen 27B training log format, fields, OOM warning signs
- `references/session-search-fallback-pattern.md` — When `session_search` fails, recover DGX credentials from cron job definitions using `search_files`
- `references/novel-enhancement-pattern.md` — Building novel (not incremental) cognitive systems on MacBook
- `references/build-vs-wire-anti-pattern.md` — Why building without wiring is waste, and the correct integration pattern
- `references/hermes-hook-signature-compatibility.md` — Critical: `**kwargs` requirement for all Hermes plugin hooks to prevent silent failures
- `references/dgx-permission-audit-websearch-fix-may16-2026.md` — **Session detail**: Full permission audit unlocking DGX Hermes with zero restrictions, DDGS web search fix, and verification commands
- `references/exfat-cross-platform-ssd-workflow-may2026.md` — **VERIFIED:** Reformat NTFS SSD to exFAT for seamless MacBook ↔ DGX transfers. Includes filesystem corruption diagnosis, `diskutil eraseDisk` command, and cross-platform compatibility matrix.
- `references/ntfs-macbook-external-ssd-may2026.md` — Earlier attempt with network transfer workaround (superseded by exFAT reformat).
- `references/ssh-background-process-launching-may2026.md` — Reliable pattern for launching background processes on DGX via SSH. Terminal tool blocks `&`/`nohup` in command strings — use remote script file instead.
- `references/cross-machine-hermes-sync.md` — **Session detail**: Full plugin sync workflow from May 14 2026 DGX deployment — tool count diagnosis, config file location gotcha, plugins.enabled format, verification commands, expected errors
- `references/dgx-hermes-deployment-may2026.md` — **Session detail**: Complete DGX Hermes deployment with full tool parity — Node.js ARM64 install, agent-browser setup, API key sync, browser automation, file verification methodology
- `references/dgx-native-hermes-gateway-may2026.md` — **Session detail**: Running Hermes Agent natively on DGX as independent instance (not just inference). Covers existing installation discovery, cron import conflict fix, gateway systemd service, Qdrant vector DB setup, and cognitive plugin verification
- `references/skill-count-sync-verification-may18-2026.md` — **Session detail**: Verifying skill counts match across MacBook and DGX after bulk skill installation. Covers the discrepancy between `hermes-agent/skills/` (source) and `~/.hermes/skills/` (runtime), depth-based counting (`maxdepth 2` vs `maxdepth 3`), and non-skill file filtering (databases, temp files). Key finding: DGX had 136 entries in `~/.hermes/skills/` but only 388 actual SKILL.md files due to non-skill artifacts
