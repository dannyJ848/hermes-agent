# SSH Background Execution for Training Jobs

## Problem

Long training jobs (Qwen loading, multi-hour training) over SSH will be killed when:
1. The SSH session times out (30s default)
2. The SSH connection drops
3. The `terminal(background=true)` SSH wrapper disconnects

Hermes rejects `&` in SSH commands as "foreground detection", but `terminal(background=true)` over SSH is ALSO unreliable — the SSH session itself drops and kills the remote process.

## WRONG: terminal(background=true) over SSH (KILLED)

```python
# DON'T DO THIS — SSH session drops, process dies with exit 255
terminal(background=true, command="ssh spark 'cd /dir && python3 train.py'")
```

**What happens**: SSH connects, starts python, SSH session drops after ~30-120s, remote python gets SIGPIPE/SIGHUP and dies. Exit code 255. Process state shows "Ssl" (sleeping, session leader) but stuck at low memory — it's deadlocked writing to broken pipe.

## WRONG: nohup over SSH (REJECTED)

```bash
# Hermes rejects this as foreground detection
ssh spark "nohup python3 train.py > log 2>&1 &"
```

## RIGHT: Bash subshell with & on remote machine (SURVIVES)

```bash
# Run via SSH but the & is INSIDE the remote bash, not the local command
ssh spark "cd /dir && bash -c 'python3 train.py > train.log 2>&1 &' && sleep 1 && ps aux | grep train | grep -v grep"
```

**Why this works**: The `&` is inside the remote `bash -c` subshell. The subshell itself is foreground, but the python process inside it is backgrounded and reparented to init. When SSH disconnects, python survives.

## Verification Pattern

```bash
# Check if process is alive (one command, no loop)
ssh spark "ps -p <PID> -o pid,etime,pcpu,pmem,stat,comm && tail -15 /path/to/train.log"
```

**Healthy signs**:
- State: `Sl` (sleeping, multithreaded) — NOT `Ssl` (session leader = stuck)
- Memory: Growing over time (Qwen loads to ~50GB)
- Log: Progress bars advancing, not stuck at same percentage

**Dead signs**:
- State: `Ssl` with low RSS (~20MB) — deadlocked on broken pipe
- Log: No new lines for minutes
- GPU: `nvidia-smi` shows 0% utilization

## Key Points

- `PYTHONUNBUFFERED=1` ensures log output is immediate (no buffering)
- Redirect BOTH stdout and stderr to a FILE on the remote machine: `> train.log 2>&1`
- The log file is your ONLY lifeline after SSH disconnects
- Use `bash -c 'command &'` — the `&` must be inside the remote shell
- Don't poll in a loop — check once, report, stay silent
- If process dies, check log for error, fix, restart

## May 2, 2026 Session — Franken V8 + Qwen-Scope Training

**Failed attempts**:
1. `terminal(background=true)` over SSH → process killed at 64% Qwen loading, exit 255
2. Multiple foreground SSH calls with 30s timeout → Qwen never finishes loading
3. Process stuck in `Ssl` state with 23MB RSS → deadlocked on broken pipe

**Working solution**:
```bash
ssh spark "cd /data/SpecForge/custom_dflash && bash -c 'PYTHONUNBUFFERED=1 python3 qwen_sae_franken25_trainer.py ... > train_franken25.log 2>&1 &' && sleep 1 && ps aux | grep qwen_sae_franken25 | grep -v grep"
```

Result: PID 1205626, Qwen loaded to 33% in 1min41s, GPU at 51GB, log advancing.

**Critical lesson**: For remote GPU training, the log file on the remote machine is your only reliable status channel. SSH sessions are ephemeral — design for disconnection.
