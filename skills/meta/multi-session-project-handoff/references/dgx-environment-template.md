# DGX Environment Template

## Connection Details

| Setting | Value | Notes |
|---------|-------|-------|
| Hostname | `spark-85e8.local` | mDNS hostname, requires same network |
| User | `djg6228` | DGX user account |
| SSH Key | `~/.ssh/dgx` or `~/.ssh/id_rsa_dgx` | Check with `ls ~/.ssh/dgx*` |
| Command | `ssh -i ~/.ssh/dgx djg6228@spark-85e8.local` | Add to ~/.ssh/config for convenience |

**SSH config shortcut:**
```
Host dgx
    HostName spark-85e8.local
    User djg6228
    IdentityFile ~/.ssh/dgx
    StrictHostKeyChecking no
```

**If SSH fails:**
1. Check key exists: `ls ~/.ssh/dgx*`
2. Check key permissions: `chmod 600 ~/.ssh/dgx`
3. Try password auth: `ssh djg6228@spark-85e8.local`
4. Check VPN if on corporate network
5. Copy scripts manually: `scp -i ~/.ssh/dgx file.py djg6228@spark-85e8.local:/data/SpecForge/custom_dflash/`

## Hardware Specs

| Component | Spec |
|-----------|------|
| GPU | NVIDIA GB10 |
| GPU Memory | 130.7 GB |
| CUDA Version | 13.0 |
| Driver | 580.142 |
| CPU | Check with `lscpu` on DGX |
| RAM | Check with `free -h` on DGX |

## Storage Paths

| Path | Purpose | Notes |
|------|---------|-------|
| `/mnt/bigssd/` | Checkpoints, logs, teacher hidden states | ~7.3 TB free. Use for ALL outputs. |
| `/data/models/` | Model weights | Read-only model storage |
| `/data/models/Qwen3.6-27B-Uncensored/` | Student model | ~50 GB |
| `/data/models/FrankenV8-25Grafts-SAE-Enhanced/` | Teacher model | ~45 GB, 11.5B params |
| `/data/models/Qwen-Scope/` | SAE weights | layer16.sae.pt, layer32.sae.pt, layer48.sae.pt |
| `/data/datasets/` | Training datasets | |
| `/data/datasets/slimorca/` | SlimOrca-200k | Ready to use |
| `/data/datasets/openhermes/` | OpenHermes-200k | Ready to use |
| `/data/SpecForge/custom_dflash/` | Training scripts | Active development directory |

## Python Environment

- Python: `python3` (system default)
- PyTorch: Pre-installed with CUDA 13.0
- Key packages: `transformers`, `torch`, `numpy`, `tqdm`

**Run scripts:** `python3 /data/SpecForge/custom_dflash/<script>.py`

## Local Machine Limitations (MacBook)

| Resource | Status |
|----------|--------|
| GPU | NONE |
| CUDA | Not available |
| `/data/` directory | Does not exist |
| Model loading | Impossible for 27B+ models |
| Training | Cannot run locally |

**DO NOT attempt to run training locally. Always use DGX.**

## Workflow

1. **Develop scripts locally** in `~/hermes-agent/training/qwen27b-sae-only/`
2. **Push to GitHub** on `qwen27b-training-artifacts-may3-2026`
3. **Pull on DGX** or `scp` scripts over
4. **Run on DGX** via SSH
5. **Monitor** with `nvidia-smi` and log files in `/mnt/bigssd/`

## Monitoring Commands

```bash
# Check if training is running
ssh dgx "ps aux | grep train_expert | grep -v grep"

# Check GPU status
ssh dgx "nvidia-smi"

# Check latest log lines
ssh dgx "tail -20 /mnt/bigssd/train_expert_logician_v4.log"

# Check disk space
ssh dgx "df -h /mnt/bigssd/"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| SSH hangs | Wait 30s — DGX may be loading models into GPU |
| "Permission denied" | `chmod 600 ~/.ssh/dgx` |
| "No route to host" | Check network/VPN |
| GPU OOM | Reduce batch size, enable gradient checkpointing |
| Root partition full | Use `/mnt/bigssd/` for ALL outputs |
| Training killed unexpectedly | Check `dmesg` for OOM killer |
