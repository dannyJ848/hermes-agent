# Axolotl Training Launch on DGX — Background Execution Pattern

## Problem

Hermes `terminal(background=true)` does NOT background processes on remote hosts — it backgrounds on the local machine. When launching axolotl training on DGX Spark via SSH, the training process dies when the SSH session closes.

## Solution

Use `execute_code` with `subprocess.run` and explicit `nohup` on the remote host:

```python
import subprocess
import time

# Launch training in background on DGX
result = subprocess.run(
    ["ssh", "djg6228@10.0.0.171",
     "source ~/train-venv/bin/activate && cd /data/SpecForge/custom_dflash && "
     "nohup bash -c 'accelerate launch -m axolotl.cli.train axolotl_config.yaml > logs/training_live.log 2>&1' > /dev/null 2>&1 & echo $!"],
    capture_output=True, text=True, timeout=30
)
pid = result.stdout.strip()
print(f"Training PID: {pid}")

# Poll to verify process started
for i in range(10):
    time.sleep(3)
    check = subprocess.run(
        ["ssh", "djg6228@10.0.0.171", f"ps -p {pid} -o pid,comm,etime | grep -v PID"],
        capture_output=True, text=True
    )
    if check.stdout.strip():
        print(f"Process running: {check.stdout.strip()}")
        break
    else:
        print(f"Check {i+1}: process not found yet...")
```

## Alternative: Direct SSH with nohup

```bash
ssh djg6228@10.0.0.171 "source ~/train-venv/bin/activate && cd /data/SpecForge/custom_dflash && nohup bash -c 'accelerate launch -m axolotl.cli.train axolotl_config.yaml > logs/training_live.log 2>&1' > /dev/null 2>&1 & echo $!"
```

## Verification

```bash
# Check process
ssh djg6228@10.0.0.171 "ps aux | grep accelerate | grep -v grep"

# Check log
ssh djg6228@10.0.0.171 "tail -20 /data/SpecForge/custom_dflash/logs/training_live.log"

# Check GPU usage
ssh djg6228@10.0.0.171 "nvidia-smi | grep -E 'GPU|MiB'"
```

## Key Pitfalls

1. **Hermes `terminal(background=true)` is local-only** — always use `nohup` on remote hosts
2. **SSH session timeout** — training may take hours; `nohup` ensures survival after disconnect
3. **Venv activation** — must source venv BEFORE running axolotl (DGX needs torch 2.11.0+cu130)
4. **Log file path** — must be absolute or relative to the cd directory
5. **PID capture** — `echo $!` must be the LAST command in the SSH string

## Preprocessing vs Training Launch

If preprocessing got stuck (speed dropped to ~80 ex/s):
- Kill preprocessing: `pkill -f 'axolotl preprocess'`
- Launch training directly — axolotl can preprocess on-the-fly
- The training launch will handle preprocessing internally
