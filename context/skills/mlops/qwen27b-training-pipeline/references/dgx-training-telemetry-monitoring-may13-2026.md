# DGX Training Telemetry and Monitoring (May 13, 2026)

## Telemetry Server

Simple HTTP server for real-time training metrics monitoring.

**File:** `/data/SpecForge/custom_dflash/telemetry_server.py`

**Endpoints:**
- `GET /health` — Server health check
- `GET /metrics` — Last 100 training metrics entries (JSON)
- `GET /status` — Current training status with staleness detection
- `GET /` — HTML dashboard with auto-refresh

**Launch:**
```bash
cd /data/SpecForge/custom_dflash
~/train-venv/bin/python telemetry_server.py
# Runs on port 8080
```

**Metrics format (written by training script):**
```json
{"step": 1, "timestamp": "2026-05-13T16:00:00", "elapsed_seconds": 120, "loss": 2.5, "learning_rate": 0.0002, "epoch": 0.1}
```

## Training Monitor Daemon

Background process that checks training health every 60 seconds.

**File:** `/data/SpecForge/custom_dflash/training_monitor.py`

**Checks:**
1. Training process alive (pgrep for train_direct.py)
2. GPU utilization (nvidia-smi)
3. GPU temperature (< 85C alert)
4. Metrics file staleness (> 5 min = alert)
5. Loss NaN detection
6. Loss explosion (> 100 = alert)

**Logs:**
- `/tmp/monitor.log` — Health check history
- `/tmp/training_alerts.log` — Alert events

## Integration with Training Script

The training script writes metrics to `training_metrics.jsonl`:

```python
class TrainingMonitor:
    def __init__(self, output_dir):
        self.metrics_file = Path(output_dir) / 'training_metrics.jsonl'
        self.start_time = time.time()
        self.step = 0
    
    def log_step(self, loss, lr, epoch=None):
        self.step += 1
        entry = {
            'step': self.step,
            'timestamp': datetime.utcnow().isoformat(),
            'elapsed_seconds': time.time() - self.start_time,
            'loss': loss,
            'learning_rate': lr
        }
        if epoch is not None:
            entry['epoch'] = epoch
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
```

## Remote Monitoring

From MacBook or other machine:
```bash
# Check health
curl http://10.0.0.171:8080/health

# Get latest metrics
curl http://10.0.0.171:8080/metrics | jq '.[-5:]'

# Get status
curl http://10.0.0.171:8080/status | jq
```

## Alert Conditions

| Condition | Action |
|-----------|--------|
| Process not running | Log ALERT, write to alert file |
| GPU loaded but idle (<5% util, >1GB mem) | Log WARNING |
| GPU temp > 85C | Log ALERT |
| Metrics stale > 5 min | Log ALERT |
| Loss is NaN | Log ALERT |
| Loss > 100 | Log ALERT |

## Pitfalls

- **Telemetry server must be started BEFORE training** — it only reads the metrics file, doesn't create it
- **Monitor daemon uses pgrep** — if training script name changes, update the pattern
- **nvidia-smi may fail under load** — monitor handles this gracefully but may miss transient issues
- **Metrics file grows unbounded** — consider log rotation for multi-day training runs
