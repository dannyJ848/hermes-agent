# DGX Spark Checkpoint - Apr 24 2026 - Phase2 Training LIVE + Monitor Active

## STATUS: Phase2 Draft Model Training RUNNING Overnight
- **Started:** Apr 24 ~22:45 CDT
- **Step:** ~40+ (Epoch 0, 0.4%)
- **Loss:** 9.875 (down from 13.125 = 24.8% improvement)
- **Speed:** ~9.3 sec/step, ETA ~26 hours for Epoch 0
- **Draft model:** 3.69B params, Muon optimizer (DeepSeek V4 style)
- **Output:** /data/models/Qwen3.6-27B-DFlash-Custom/

## MONITOR ACTIVE
- **Monitor PID:** 16614 on Spark
- **Status file:** /tmp/phase2_monitor_status.json (updated every 30s)
- **Log:** /tmp/monitor.log
- **Alerts:** Process death, GPU overheat, loss explosion, NaN, step stalls

## CLEANUP DONE
- Deleted old Qwen3.6-35B-A3B-DFlash model (905MB)
- Cleared triton cache, temp files
- Docker prune (0B reclaimed — images minimal)
- Disk: 53G free (99% full, tight but sufficient)

## RESUME COMMAND (if needed):
```bash
ssh djg6228@10.0.0.171
cat /tmp/phase2_monitor_status.json  # Check status
tail -20 /tmp/phase2_train.log       # Training progress
```

## FILES:
- Training script: /data/SpecForge/custom_dflash/phase2_train_draft.py
- Monitor: /data/SpecForge/custom_dflash/monitor.py
- Log: /tmp/phase2_train.log
- Output dir: /data/models/Qwen3.6-27B-DFlash-Custom/

## CONTEXT:
- Hermes v0.11.0
- DGX Spark: GB10/Blackwell SM121, 128GB unified memory
- vLLM NOT running (stopped for training)
- All 6 training datasets on disk (~475GB)
- Phase1 hidden states: 10,000/10,000 complete (424GB)
