# DGX Training Monitoring — Session-Specific Reference

## SSH Connection (ALWAYS CHECK THIS FIRST)

The DGX Spark SSH config is NOT in `~/.ssh/config` directly. It's in:
```
~/.ssh/config  →  Include "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/ssh_config"
```

That file contains:
```
Host spark-85e8.local
  Hostname spark-85e8.local
  User djg6228
  Port 22
  IdentityFile "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key"
```

Also resolves via IP: `10.0.0.171`

**Pitfall**: Asking user for connection details when the config already exists. Always check `~/.ssh/config` and any Include directives before asking.

## Live Status Pull Command

```bash
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
  -i "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key" \
  djg6228@spark-85e8.local \
  "grep 'Step [0-9]\+/10000' /mnt/bigssd/train_r256_final.log | tail -1 \
   && echo '---GPU---' \
   && nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,noheader,nounits \
   && echo '---PID---' \
   && ps -p \$(pgrep -f train_lora) -o pid,ppid,%cpu,%mem,etime,comm \
   && echo '---CHECKPOINTS---' \
   && ls -lt /data/SpecForge/custom_dflash/checkpoints/ | head -3"
```

## Memory Reconciliation (Three Metrics)

| Metric | Source | What It Means | Typical Value |
|--------|--------|---------------|---------------|
| Active tensors | Training log `GPU: 62.6GB` | Model weights + optimizer states + active gradients | 62.6GB |
| Process memory | `nvidia-smi -q \| grep "Used GPU Memory"` | Full CUDA allocation including context, buffers, cache | ~93GB |
| System RAM | DGX dashboard | Host memory for data loaders, CPU offload, OS | 116.5/128GB |

**Key insight**: The training log under-reports by ~30GB. The GB10 driver reports N/A for total VRAM, so use process-level `Used GPU Memory` to track actual allocation. Memory oscillates 0→93→0 during steps — this is normal buffer allocation, not a leak.

## Screenshot Handling (macOS)

Screenshots saved to `/var/folders/.../TemporaryItems/NSIRD_screencaptureui_*/` cannot be read directly by `vision_analyze`. Always copy to accessible path first:

```python
import shutil, glob
matches = glob.glob("/var/folders/*/TemporaryItems/NSIRD_screencaptureui_*/Screenshot*.png")
for m in matches:
    shutil.copy(m, os.path.expanduser("~/Desktop/dgx_screenshot.png"))
```

Then use `vision_analyze` with `~/Desktop/dgx_screenshot.png`.

## Status Update Workflow

1. Pull live status from DGX (SSH command above)
2. Update `instant_context.py` with new step/loss/ETA
3. Update knowledge base at `~/.hermes/knowledge/qwen27b-training-final-state.md`
4. Update memory with live state
5. Update goals (complete old, add new)
6. Git commit + push `instant_context.py`
7. SCP updated `instant_context.py` to DGX
8. Update `MASTER_DOC.md` on DGX

## Training Log Format

```
Step NNNN/10000 | Loss: X.XXXX (CE:X.XXX D:X.XXX SAE:X.XXX) | W:(W1,W2,W3) | LR: X.XXe-XX | GPU: XX.XGB
```

Loss components:
- CE: Cross-entropy (primary)
- D: Distillation (teacher)
- SAE: Sparse autoencoder guidance
- W: Loss weights (CE, distill, SAE)
