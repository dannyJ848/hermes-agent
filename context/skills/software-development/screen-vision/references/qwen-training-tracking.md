# Qwen 27B Training Tracking Pattern

## How to Check Training Progress

```bash
# Latest steps
ssh djg6228@spark-85e8.local "grep 'Step [0-9]*/10000' /mnt/bigssd/train_r256_final.log | tail -5"

# Current process
ssh djg6228@spark-85e8.local "ps aux | grep -E 'python.*train|axolotl' | grep -v grep"

# Full log tail
ssh djg6228@spark-85e8.local "tail -20 /mnt/bigssd/train_r256_final.log"
```

## ETA Calculation

From two log entries with timestamps and step numbers:
```python
from datetime import datetime

start = datetime.strptime("14:50:21", "%H:%M:%S")
end = datetime.strptime("15:03:49", "%H:%M:%S")
delta_seconds = (end - start).total_seconds()
steps_done = 5320 - 5280  # 40 steps

sec_per_step = delta_seconds / steps_done
remaining = 10000 - 5320
eta_hours = (remaining * sec_per_step) / 3600
```

## Current Status (May 9, 2026)
- Step: 5320/10000 (53.2%)
- Speed: ~20.2 sec/step
- ETA: ~26 hours
- Loss: 1.2457 (CE:1.060 D:1.154 SAE:0.508)
- GPU: 62.6GB
- PID: 443609

## When Training Completes
1. Push training data to DGX: `~/qwen-training-data/` (1.8MB)
2. Deploy with vLLM on `spark-85e8.local:8000`
3. Update hermes vision config to point to local endpoint
4. Test `vision_analyze` with local Qwen model

## Historical Checkpoints
- Step 1560/10000 (~46h ETA) — old estimate from earlier session
- Step 5320/10000 (~26h ETA) — current reality
