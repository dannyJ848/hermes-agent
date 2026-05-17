# SSH Timeout on DGX Under Load — May 17, 2026

## Problem

When DGX Spark is running vLLM inference or model training, SSH commands from MacBook timeout with `[Command interrupted]` or hang indefinitely.

## Root Cause

GPU at 97%+ utilization starves the system scheduler. SSH daemon cannot get CPU time to respond to connection requests or execute commands.

## Symptoms vs Causes

| Symptom | Likely Cause | Test |
|---------|-------------|------|
| `ping spark-85e8.local` fails | Network down / DGX off | Check power LED |
| `ping` works, SSH hangs | DGX under load | Wait 5-10 min |
| SSH connects, commands hang | Specific process consuming CPU | Check via serial console |
| Intermittent failures | Thermal throttling or power fluctuation | Check `nvidia-smi` temp |

## Recovery

1. **Wait it out**: 5-10 minutes for inference/training to complete a batch
2. **Fail fast**: Use `ssh -o ConnectTimeout=5` to avoid indefinite hangs
3. **Power cycle**: Last resort if DGX is completely unresponsive
4. **Serial console**: If available, use USB-C debug connection

## Prevention

- Use `screen` or `tmux` for ALL long-running processes
- Start vLLM/training inside screen, detach immediately
- Batch monitoring commands: `ssh host "cmd1; cmd2; cmd3"` instead of 3 separate SSH calls
- Use `nohup` for one-off background tasks
- Avoid monitoring during model loading (highest load period)

## What NOT to do

- ❌ Don't repeatedly retry SSH commands — each attempt adds load
- ❌ Don't run `ps aux` or `top` during high load — these make it worse
- ❌ Don't assume network is down and cycle power immediately
- ❌ Don't use terminal tool with default timeout — set explicit short timeouts

## Session Context

- Date: May 17, 2026
- DGX running: vLLM with Qwen3.6-27B-Uncensored + DFlash speculative decoding
- MacBook SSH to spark-85e8.local
- All terminal commands returned `[Command interrupted]` after working earlier
- vLLM container still running (confirmed before timeout cascade)
- Screen session `hermes_auto` was manually stopped, but vLLM remained running
