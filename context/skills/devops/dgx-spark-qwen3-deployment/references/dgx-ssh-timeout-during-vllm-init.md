# DGX SSH Timeout During vLLM Initialization

## Problem

When vLLM starts up with large models (Qwen3.6-27B, 53GB+), the DGX becomes completely unresponsive to SSH connections during:
1. Model weight loading to GPU (~2-3 minutes)
2. torch.compile compilation (~1-2 minutes)
3. CUDA graph capture (~5-10 minutes total)

Symptoms:
- SSH connections hang at "banner exchange" or timeout
- ping works but SSH fails
- System appears "frozen" from remote perspective
- After ~10 minutes, system becomes responsive again

## Root Cause

vLLM initialization is CPU-intensive and memory-bandwidth-intensive:
- Loading 53GB model weights from SSD to GPU
- torch.compile doing JIT compilation with Dynamo/Inductor
- CUDA graph capture running 96+ iterations for warmup

This consumes all available CPU cycles and I/O bandwidth, leaving SSH daemon starved.

## Timeline (Qwen3.6-27B + DFlash draft)

| Phase | Duration | SSH Responsive? |
|-------|----------|----------------|
| Container start | 0-30s | ✅ Yes |
| Model weight loading | 30s-3min | ⚠️ Slow |
| torch.compile (backbone) | 3-5min | ❌ No |
| torch.compile (eagle_head) | 5-7min | ❌ No |
| CUDA graph capture (PIECEWISE) | 7-10min | ❌ No |
| CUDA graph capture (FULL) | 10-12min | ❌ No |
| **Ready** | **~12-15min total** | **✅ Yes** |

## Workarounds

### 1. Wait It Out (Recommended)

Simply wait 12-15 minutes after starting vLLM before attempting SSH. The system will recover automatically.

### 2. Use systemd Service with Restart

Configure Hermes as a systemd service that auto-starts after vLLM:
```ini
[Unit]
After=docker.service
Wants=vllm.service

[Service]
Restart=always
RestartSec=30
```

### 3. Reduce CUDA Graph Capture

Disable or reduce CUDA graph capture to shorten initialization:
```bash
--enforce-eager  # Disables CUDA graphs entirely (slower inference)
# OR
--max-seq-len-to-capture 8192  # Default, smaller graphs
```

Trade-off: Slower inference per request but faster startup.

### 4. Pre-compile Models

Use vLLM's compilation cache to skip torch.compile on subsequent runs:
```bash
# First run compiles and caches
# Subsequent runs load from ~/.cache/vllm/torch_compile_cache/
```

Cache persists across container restarts if using persistent volumes.

## What NOT to Do

- ❌ Power cycle the DGX during initialization — corrupts nothing but wastes 15+ minutes
- ❌ Kill the vLLM container — restart from scratch
- ❌ Run multiple SSH attempts — adds load to already stressed system

## Recovery After Power Cycle

If DGX was power cycled during vLLM initialization:
1. Wait for DGX to fully boot (~2-3 minutes)
2. Verify network: `ping 10.0.0.171`
3. Verify SSH: `ssh djg6228@10.0.0.171 echo OK`
4. Check if vLLM auto-started (if configured via systemd)
5. If not, manually start vLLM container
6. Wait 12-15 minutes for full initialization
7. Verify: `curl http://localhost:8000/v1/models`

## Session Reference

- Date: May 16, 2026
- Model: Qwen3.6-27B-Uncensored (53GB) + Qwen3.5-27B-DFlash draft
- Hardware: DGX Spark (GB10, 128GB unified memory)
- Observed: SSH timeout during banner exchange at ~5-10min mark
- Recovery: System responsive after ~15min total initialization
