# Terminal Tool Background Execution Pattern

Session: May 10-11, 2026 — Qwen 27B benchmark evaluation on DGX Spark

## The Problem

The Hermes `terminal` tool blocks shell-level background wrappers (`nohup`, `disown`, `setsid`, `&`). Attempting to use them inside a command fails silently or produces unexpected behavior.

**WRONG — foreground SSH with nohup inside:**
```bash
# This will NOT background properly — the terminal tool blocks nohup
ssh djg6228@10.0.0.171 "nohup lm_eval --tasks mmlu ... > log.txt 2>&1 &"
```

**WRONG — attempting to disown:**
```bash
ssh djg6228@10.0.0.171 "bash -c 'nohup lm_eval ... & disown'"
# Same problem — shell-level backgrounding is blocked
```

## The Solution

Use `terminal(background=true)` which backgrounds the **entire SSH session**, not processes inside it. The SSH session persists on the remote host even if the local terminal tool call completes.

**CORRECT — background the SSH session itself:**
```bash
terminal(background=true, command="ssh djg6228@10.0.0.171 'bash -c \"cd /project && source venv/bin/activate && lm_eval --tasks mmlu ... && lm_eval --tasks gsm8k ... && ...\"'")
```

Key points:
1. The SSH session itself runs in the background
2. Commands inside the SSH session run sequentially (not backgrounded)
3. The session persists until all commands complete or the remote host reboots
4. You can disconnect and reconnect — the SSH session survives

## Status Monitoring for Background SSH Sessions

Since you can't wait on the background process handle, use `execute_code` with SSH for clean status checks:

```python
import subprocess

result = subprocess.run(
    ['ssh', 'djg6228@10.0.0.171',
     'ps -o pid,pcpu,pmem,etime,comm -p <PID> | tail -1 && '
     'nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,noheader,nounits && '
     'grep -o "Running loglikelihood requests: *[0-9]*%" /path/to/benchmark_suite.log | tail -1'],
    capture_output=True, text=True, timeout=15
)
print(result.stdout)
```

## When to Use This Pattern

- Long-running model evaluations (lm-eval-harness, MMLU, GSM8K)
- Training jobs that exceed SSH timeout
- Any command that takes >30 minutes and runs on a remote host
- Benchmark suites that run sequentially

## When NOT to Use This Pattern

- Commands that need interactive input
- Commands where you need immediate output
- Short commands (<5 minutes) — just use regular `terminal`
- Commands that need to be killed from the local side (use `execute_code` with SSH to send kill signals)

## Related Patterns

- `dgx-spark-qwen3-deployment:references/post-training-evaluation-patterns.md` — Full evaluation workflow
- `qwen27b-dgx-deployment` — Qwen 27B specific evaluation patterns
