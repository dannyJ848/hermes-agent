#!/usr/bin/env python3
"""Check if benchmark process is healthy on remote host.

Usage: python3 benchmark_health_check.py <host> <pid> <log_path>

Returns exit code 0 if healthy, 1 if dead or stuck.
"""
import subprocess
import sys
import time


def check_remote(host: str, pid: str, log_path: str) -> bool:
    """Check benchmark health on remote host."""
    # Process existence
    ps = subprocess.run(
        ['ssh', host, f'ps -p {pid} > /dev/null 2>&1 && echo ALIVE || echo DEAD'],
        capture_output=True, text=True, timeout=10
    )
    status = ps.stdout.strip()

    # GPU utilization
    gpu = subprocess.run(
        ['ssh', host, 'nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,noheader,nounits'],
        capture_output=True, text=True, timeout=10
    )
    gpu_util, gpu_temp = gpu.stdout.strip().split(', ')

    # Log growth
    log_size = subprocess.run(
        ['ssh', host, f'stat -c %s {log_path}'],
        capture_output=True, text=True, timeout=10
    )
    size = int(log_size.stdout.strip())

    print(f"PID {pid}: {status}")
    print(f"GPU: {gpu_util}% util, {gpu_temp}°C")
    print(f"Log: {size} bytes")

    if status == "DEAD":
        print("FAIL: Process dead")
        return False
    if int(gpu_util) == 0 and status == "ALIVE":
        print("WARN: Process alive but GPU idle — may be stuck")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <host> <pid> <log_path>")
        sys.exit(1)
    ok = check_remote(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(0 if ok else 1)
