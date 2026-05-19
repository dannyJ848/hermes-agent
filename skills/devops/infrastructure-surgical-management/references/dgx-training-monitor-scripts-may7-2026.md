# DGX Training Monitor & Auto-Resume Scripts — May 7, 2026

## Deployment

Deployed on DGX Spark for unattended training of Qwen 27B with rank-256 LoRA.

### Remote (DGX)
- `/data/SpecForge/custom_dflash/training_monitor.sh` — checks PID, GPU, checkpoint age, triggers resume
- `/data/SpecForge/custom_dflash/resume_training.sh` — kills, clears GPU, restarts from latest valid checkpoint
- `/data/SpecForge/custom_dflash/monitor_config.json` — config (PID 180722, 30 min idle threshold)
- DGX crontab: `*/5 * * * * /data/SpecForge/custom_dflash/training_monitor.sh`

### Local (Mac)
- `/tmp/dgx_local_monitor.sh` — SSH-triggers remote monitor, logs to `/tmp/dgx_monitor.log`

## Key Design Decisions

1. **Checkpoint validation**: Resume script checks for actual weight files, not just directory existence
2. **OOM prevention**: Resume script includes `empty_cache()`, `synchronize()`, CPU offload for saves
3. **PID tracking**: monitor_config.json stores expected PID; if PID dies, trigger resume
4. **Idle detection**: If GPU utilization <10% for 30 min, assume hung, trigger resume
5. **Log rotation**: monitor.log capped at 10MB to prevent disk fill

## Why these scripts exist

Training at GPU memory edge (62.6GB/130GB used, 91-95GB peak) is fragile:
- Checkpoint saves are OOM hazards
- SSH becomes unresponsive during heavy load
- Process can hang without crashing
- Manual monitoring is impossible (user sleeps, DGX is remote)

Auto-monitor handles all failure modes without human intervention.

## Integration with loop guard

When checking training status manually, NEVER make more than 2 SSH calls. The monitor scripts handle continuous monitoring; human checks should be sparse status reads only.
