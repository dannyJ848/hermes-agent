# DeepSpeed ZeRO-Infinity Debugging on DGX Spark

Session: May 2, 2026
Context: Full fine-tuning Qwen 3.6 27B (all params trainable) with Franken V8 teacher + Qwen-Scope SAEs
Hardware: DGX Spark, 130GB unified memory, NVMe SSD offload (/mnt/bigssd)

## Bug 1: async_io op missing .so shared library

**Symptom:** DeepSpeed initialization hangs or fails with async_io-related errors.
**Root cause:** Torch extensions cache has compiled `.o` object files but no `.so` shared library.
**Fix:**
```bash
# Clear the torch extensions cache
rm -rf ~/.cache/torch_extensions/py312_cu130/async_io

# Rebuild with async_io enabled
DS_BUILD_AIO=1 pip install deepspeed --force-reinstall --no-cache-dir

# Verify
ls -la ~/.cache/torch_extensions/py312_cu130/async_io/async_io.so
# Should show ~27MB .so file
```

## Bug 2: "More elements than buffer size" assertion

**Symptom:** `AssertionError: More elements 1271398400 than buffer size 100000000` in `partitioned_param_swapper.py:357`
**Root cause:** Qwen 27B's largest parameter (embedding layer) has 1.27B elements, but default `buffer_size=100000000` (100M).
**Critical config detail:** `buffer_size` is valid in `offload_param` (DeepSpeedZeroOffloadParamConfig) but NOT in `offload_optimizer` (DeepSpeedZeroOffloadOptimizerConfig). Setting it on `offload_optimizer` silently fails or is ignored.

**Correct config:**
```json
{
  "zero_optimization": {
    "stage": 3,
    "offload_optimizer": {
      "device": "nvme",
      "nvme_path": "/mnt/bigssd/deepspeed_offload",
      "pin_memory": true
    },
    "offload_param": {
      "device": "nvme",
      "nvme_path": "/mnt/bigssd/deepspeed_offload",
      "pin_memory": true,
      "buffer_size": 2000000000
    }
  }
}
```

**Buffer size rule:** Set `buffer_size` to at least 2x the largest single parameter's element count. For Qwen 27B: 1.27B elements → buffer_size >= 2_000_000_000.

## Current Status (May 2, 2026)

- async_io: FIXED
- buffer_size config: FIXED
- 51GB of parameter swap files successfully written to `/mnt/bigssd/deepspeed_test/zero_stage_3/bfloat16params/`
- Process exited before completion — need to verify if full init completes and test forward+backward pass

## Key Paths

- Test script: `/data/SpecForge/custom_dflash/test_deepspeed_minimal.py`
- Trainer: `/data/SpecForge/custom_dflash/qwen36_franken_fullft_deepspeed.py`
- Offload dir: `/mnt/bigssd/deepspeed_test/` (test) / `/mnt/bigssd/deepspeed_offload/` (production)
