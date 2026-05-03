import subprocess
import re
import os

REMOTE_HOST = "djg6228@10.0.0.171"
LOG_FILE = "/tmp/phase2_train.log"
TRAINING_SCRIPT = "phase2_train_draft.py"
CHECKPOINT_DIR = "/data/models/Qwen3.6-27B-DFlash-Custom"

def run_remote_command(command):
    try:
        # Using a timeout to prevent hanging. Increased to 60s for potentially slow SSH connections/commands.
        result = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", REMOTE_HOST, command], # BatchMode prevents password prompts
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, f"Command failed: {e.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return None, "Command timed out."
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"

def check_training_process():
    output, error = run_remote_command(f"pgrep -f {TRAINING_SCRIPT}")
    if error:
        return False, "Process check error", error
    if output:
        return True, "Running", None
    return False, "Not Running", None

def get_training_progress():
    # Get last 100 lines for a better chance to find the latest progress, especially if logs are verbose.
    output, error = run_remote_command(f"tail -n 100 {LOG_FILE}")
    if error:
        return "N/A", "N/A", error

    step = "N/A"
    loss = "N/A"
    
    # Regex to find "step=X, loss=Y" pattern from tqdm output
    step_loss_pattern = re.compile(r"step=(\d+).*?loss=([\d\.]+)")
    
    latest_match = None
    for line in output.splitlines():
        match = step_loss_pattern.search(line)
        if match:
            latest_match = match
            
    if latest_match:
        step = latest_match.group(1)
        loss = latest_match.group(2)

    return step, loss, None

def check_disk_space():
    output, error = run_remote_command("df -h /")
    if error:
        return "N/A", error

    match = re.search(r"(\d+)%", output)
    if match:
        return match.group(1), None
    return "N/A", "Could not parse disk space from df -h / output."

def check_gpu_utilization():
    output, error = run_remote_command("nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits")
    if error:
        return "N/A", error
    
    # Output is typically a number like "50" (for 50%). Take the first value if multiple GPUs.
    gpu_values = re.findall(r'\d+', output)
    if gpu_values:
        return gpu_values[0], None # Report utilization of the first GPU
    return "N/A", "Could not parse GPU utilization from nvidia-smi output."

def verify_checkpoint(current_step):
    # Placeholder for checkpoint verification logic.
    # This assumes checkpoints are named like 'checkpoint_step_<step_number>.pth'
    # and saved in CHECKPOINT_DIR.
    
    if current_step == "N/A":
        return "Cannot verify checkpoint: training step is N/A."
        
    try:
        step_int = int(current_step)
    except ValueError:
        return f"Cannot verify checkpoint: invalid step value '{current_step}'."

    if step_int <= 0:
        return "N/A" # No need to check checkpoints for very early steps

    if step_int % 500 == 0:
        # Example: check for a file named like 'checkpoint_step_500.pth'
        expected_checkpoint_file = os.path.join(CHECKPOINT_DIR, f"checkpoint-{step_int}.pt")
        check_command = f"[ -f {expected_checkpoint_file} ] && echo 'Exists' || echo 'Missing'"
        
        check_result, error = run_remote_command(check_command)
        if error:
            return f"Checkpoint verification error: {error}"
            
        if "Exists" in check_result:
            return f"Checkpoint for step {step_int} present."
        else:
            return f"Checkpoint for step {step_int} MISSING! Expected: {expected_checkpoint_file}"
    return "N/A"

def main():
    alerts = []
    
    # 1. Check training process
    is_running, process_status_msg, process_error = check_training_process()
    if process_error:
        alerts.append(f"Process check error: {process_error}")
    elif not is_running:
        alerts.append("Training process is not running!")

    # 2. Get training progress
    step, loss, log_error = get_training_progress()
    if log_error:
        alerts.append(f"Log reading error: {log_error}")

    # 3. Check disk space
    disk_usage, disk_error = check_disk_space()
    if disk_error:
        alerts.append(f"Disk check error: {disk_error}")
    elif disk_usage != "N/A" and int(disk_usage) > 90: # Alert if disk usage > 90%
        alerts.append(f"High disk usage: {disk_usage}%")

    # 4. Check GPU utilization
    gpu_util, gpu_error = check_gpu_utilization()
    if gpu_error:
        alerts.append(f"GPU check error: {gpu_error}")
    elif gpu_util != "N/A" and int(gpu_util) < 5: # Example alert: GPU utilization too low (e.g., if training stalled)
        if is_running: # Only alert if process is running but GPU is low
            alerts.append(f"Low GPU utilization: {gpu_util}% while process is running.")

    # 5. Verify checkpoint
    checkpoint_status = verify_checkpoint(step)
    if "MISSING" in checkpoint_status or "error" in checkpoint_status.lower() or "Cannot verify" in checkpoint_status:
        alerts.append(checkpoint_status)
    elif "present" in checkpoint_status:
        pass # No alert if checkpoint is present
    
    # Concise output
    status_line = f"Status: {process_status_msg}"
    step_line = f"Step: {step}"
    loss_line = f"Loss: {loss}"
    disk_line = f"Disk: {disk_usage}%"
    gpu_line = f"GPU: {gpu_util}%"
    alerts_line = f"Alerts: {', '.join(alerts) if alerts else 'None'}"

    print(f"{status_line}, {step_line}, {loss_line}, {disk_line}, {gpu_line}, {alerts_line}")

if __name__ == "__main__":
    main()
