# qwen27b-training-session-update-may8-2290

*Researched: 2026-05-08 22:16 CDT*

# Qwen 27B Expert Logician — Session Update May 8, 2026

## Training Progress
- Step 2290/10000 (22.9%) — up from 1560 at session start
- Loss: 1.5435 (CE:1.282, D:1.359, SAE:0.592) — down from ~3.0
- GPU: NVIDIA GB10, process memory oscillates 0-93GB (normal behavior)
- Training log "GPU: 62.6GB" tracks active tensors only, not full CUDA allocation
- System RAM: 116.5/128GB near saturation — expected for this workload
- ETA: ~35 hours remaining

## Key Discovery
The training log's GPU memory reading (62.6GB) significantly under-reports actual GPU allocation (~93GB per nvidia-smi). The discrepancy is:
- 62.6GB = model weights + optimizer states + active tensors (what training code tracks)
- 93GB = full process allocation including CUDA context, SAE buffers, distillation caches, PyTorch allocator overhead
- Memory oscillates 0→93→0 during steps as buffers are allocated/freed — this is normal, not a leak

## DGX Connection Details
- SSH: djg6228@spark-85e8.local (or 10.0.0.171)
- Key: /Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key
- Found in: ~/.ssh/config Include directive for NVIDIA Sync

## Files Updated
- Knowledge base: ~/.hermes/knowledge/qwen27b-training-final-state.md
- Memory: Updated with live state (step 2290, loss 1.5435, memory oscillation note)
- Goals: Completed old step 1560 goal, added new step 2290 goal


## Sources

- https://github.com/dannyJ848/hermes-agent/blob/qwen27b-training-artifacts-may3-2026/instant_context.py
