# DGX Environment & Connection Details

## ⚠️ CRITICAL: This is a remote GPU machine. Local MacBook has NO GPU.

---

## Connection

| Setting | Value |
|---------|-------|
| Hostname | `spark-85e8.local` |
| User | `djg6228` |
| SSH Key | `~/.ssh/dgx` or `~/.ssh/id_rsa_dgx` |
| Command | `ssh -i ~/.ssh/dgx djg6228@spark-85e8.local` |

**If SSH fails:**
1. Check key exists: `ls ~/.ssh/dgx*`
2. Try without key (password auth): `ssh djg6228@spark-85e8.local`
3. Check VPN if on corporate network
4. Alternative: Copy scripts via `scp` and run manually on DGX

---

## Hardware

| Component | Spec |
|-----------|------|
| GPU | NVIDIA GB10 |
| GPU Memory | 130.7 GB |
| CUDA Version | 13.0 |
| Driver | 580.142 |

**Current Status:** Check with `nvidia-smi` after SSH

---

## Storage Paths

| Path | Purpose | Free Space |
|------|---------|------------|
| `/mnt/bigssd/` | Checkpoints, logs, teacher hidden states | ~7.3 TB |
| `/data/models/` | Model weights (Qwen, Franken V8, SAEs) | Check on DGX |
| `/data/datasets/` | Training datasets | Check on DGX |
| `/data/SpecForge/custom_dflash/` | Training scripts location | N/A |

**Critical subdirectories:**
- `/data/models/Qwen3.6-27B-Uncensored/` — Student model
- `/data/models/FrankenV8-25Grafts-SAE-Enhanced/` — Teacher (11.5B params)
- `/data/models/Qwen-Scope/` — SAE weights (layer16, 32, 48)
- `/data/datasets/slimorca/` — SlimOrca-200k
- `/data/datasets/openhermes/` — OpenHermes-200k

---

## Python Environment on DGX

- Python: `python3` (system default)
- PyTorch: Pre-installed with CUDA 13.0
- Key packages: `transformers`, `torch`, `numpy`, `tqdm`

**Run scripts with:** `python3 /data/SpecForge/custom_dflash/<script>.py`

---

## Local MacBook Limitations

| Resource | Status |
|----------|--------|
| GPU | NONE |
| CUDA | Not available |
| /data/ directory | Does not exist |
| Model loading | Impossible for 27B+ models |

**DO NOT attempt to run training locally.** Always use DGX.

---

## Workflow

1. **Develop scripts locally** in `~/hermes-agent/training/qwen27b-sae-only/`
2. **Push to GitHub** on `qwen27b-training-artifacts-may3-2026`
3. **Pull on DGX** or `scp` scripts over
4. **Run on DGX** via SSH
5. **Monitor** with `nvidia-smi` and log files

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| SSH hangs | Wait 30s, DGX may be loading models |
| "Permission denied" | Check SSH key permissions: `chmod 600 ~/.ssh/dgx` |
| "No route to host" | Check network/VPN |
| GPU OOM | Reduce batch size, enable gradient checkpointing |
| Root partition full | Use `/mnt/bigssd/` for ALL outputs |

---

## Last Known State (May 3, 2026 ~19:15 CDT)

- Previous training killed at step 50/1000
- GPU clean and ready
- 8+ scripts in repo, ready to run
- See MASTER_PLAN.md for current phase and next steps
