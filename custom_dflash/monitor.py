#!/usr/bin/env python3
"""
Real-time training monitor for Phase2 DFlash draft model training.
Monitors log file, GPU stats, and process health. Alerts on anomalies.
"""

import os
import sys
import time
import json
import subprocess
import signal
from datetime import datetime

LOG_FILE = "/tmp/phase2_train.log"
STATUS_FILE = "/tmp/phase2_monitor_status.json"
CHECK_INTERVAL = 30  # seconds

# Anomaly thresholds
MAX_STEP_TIME = 120  # seconds per step (stuck detection)
MAX_LOSS = 20.0  # loss explosion
MIN_LOSS_IMPROVEMENT_EPOCH = 0.5  # min loss drop per epoch
MAX_GPU_TEMP = 85  # celsius
MIN_GPU_UTIL = 10  # percent (training should use GPU)

def get_gpu_stats():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            temp, util, mem_used, mem_total = result.stdout.strip().split(", ")
            return {
                "temp": int(temp),
                "util": int(util),
                "mem_used": int(mem_used),
                "mem_total": int(mem_total),
            }
    except Exception:
        pass
    return None

def get_process_info():
    try:
        result = subprocess.run(
            ["pgrep", "-f", "phase2_train_draft.py"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid:
                    # Get CPU/memory
                    ps_result = subprocess.run(
                        ["ps", "-p", pid, "-o", "%cpu,%mem,etime"],
                        capture_output=True, text=True, timeout=5
                    )
                    if ps_result.returncode == 0:
                        lines = ps_result.stdout.strip().split("\n")
                        if len(lines) >= 2:
                            cpu, mem, etime = lines[1].split()
                            return {
                                "pid": pid,
                                "cpu": float(cpu),
                                "mem": float(mem),
                                "etime": etime,
                            }
    except Exception:
        pass
    return None

def parse_log_tail(lines=20):
    try:
        with open(LOG_FILE, "r") as f:
            content = f.read()
            all_lines = content.split("\n")
            return all_lines[-lines:]
    except Exception:
        return []

def extract_loss_from_line(line):
    """Extract loss value from tqdm log line."""
    if "loss=" in line:
        try:
            parts = line.split("loss=")
            if len(parts) >= 2:
                loss_str = parts[1].split(",")[0].split("]")[0].strip()
                return float(loss_str)
        except Exception:
            pass
    return None

def extract_step_from_line(line):
    """Extract step number from tqdm log line."""
    if "step=" in line:
        try:
            parts = line.split("step=")
            if len(parts) >= 2:
                step_str = parts[1].split(",")[0].split("]")[0].strip()
                return int(step_str)
        except Exception:
            pass
    return None

def check_anomalies(current_step, current_loss, last_step_time, gpu_stats, proc_info):
    alerts = []
    
    # Process died
    if proc_info is None:
        alerts.append("CRITICAL: Training process not found!")
    
    # GPU issues
    if gpu_stats:
        if gpu_stats["temp"] > MAX_GPU_TEMP:
            alerts.append(f"WARNING: GPU temp {gpu_stats['temp']}C > {MAX_GPU_TEMP}C")
        if gpu_stats["util"] < MIN_GPU_UTIL and current_step > 10:
            alerts.append(f"WARNING: GPU util {gpu_stats['util']}% < {MIN_GPU_UTIL}% (training stalled?)")
    
    # Step time (stuck detection)
    if last_step_time and last_step_time > MAX_STEP_TIME:
        alerts.append(f"WARNING: Step time {last_step_time:.1f}s > {MAX_STEP_TIME}s (stuck?)")
    
    # Loss explosion
    if current_loss and current_loss > MAX_LOSS:
        alerts.append(f"CRITICAL: Loss {current_loss:.2f} > {MAX_LOSS} (explosion?)")
    
    # Loss NaN
    if current_loss and current_loss != current_loss:  # NaN check
        alerts.append("CRITICAL: Loss is NaN!")
    
    return alerts

def main():
    print(f"[{datetime.now()}] Phase2 Training Monitor Started")
    print(f"Monitoring: {LOG_FILE}")
    print(f"Check interval: {CHECK_INTERVAL}s")
    print(f"Press Ctrl+C to stop\n")
    
    last_step = 0
    last_step_time = None
    step_start_time = None
    epoch_losses = {}
    
    try:
        while True:
            now = time.time()
            
            # Parse log
            log_lines = parse_log_tail(10)
            current_loss = None
            current_step = last_step
            
            for line in log_lines:
                loss = extract_loss_from_line(line)
                if loss is not None:
                    current_loss = loss
                step = extract_step_from_line(line)
                if step is not None:
                    current_step = step
            
            # Track step timing
            if current_step > last_step:
                if step_start_time:
                    last_step_time = now - step_start_time
                step_start_time = now
                last_step = current_step
            
            # Get system stats
            gpu_stats = get_gpu_stats()
            proc_info = get_process_info()
            
            # Check anomalies
            alerts = check_anomalies(current_step, current_loss, last_step_time, gpu_stats, proc_info)
            
            # Build status
            status = {
                "timestamp": datetime.now().isoformat(),
                "step": current_step,
                "loss": current_loss,
                "step_time": last_step_time,
                "gpu": gpu_stats,
                "process": proc_info,
                "alerts": alerts,
            }
            
            # Save status
            with open(STATUS_FILE, "w") as f:
                json.dump(status, f, indent=2)
            
            # Print summary
            gpu_str = f"GPU {gpu_stats['temp']}C {gpu_stats['util']}% {gpu_stats['mem_used']}/{gpu_stats['mem_total']}MB" if gpu_stats else "GPU N/A"
            loss_str = f"loss={current_loss:.4f}" if current_loss else "loss=N/A"
            step_str = f"step={current_step}"
            time_str = f"{last_step_time:.1f}s/step" if last_step_time else "N/A"
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {step_str} {loss_str} {time_str} | {gpu_str}")
            
            # Print alerts
            for alert in alerts:
                print(f"  >>> ALERT: {alert}")
            
            # Sleep
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Monitor stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
