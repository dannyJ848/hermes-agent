# DGX Spark Gotchas 63-66 (Reddit Deep Scan, Apr 18 2026)

63. **UNSLOTH_MOE_BACKEND=grouped_mm for 12x faster MoE training.**
    Unsloth's new Triton+grouped_mm MoE kernels give 12x faster training
    with 35% less VRAM on T4+ GPUs (including GH200). The backend auto-
    selects but should be explicitly set. `grouped_mm` uses torch._grouped_mm
    (requires Transformers v5+). `unsloth_triton` = fallback for A100/older
    PyTorch. `native_torch` = 12x slower but always works.
    Source: unsloth.ai/docs/basics/faster-moe + r/LocalLLaMA
    FIX: Add `export UNSLOTH_MOE_BACKEND="grouped_mm"` before training.

64. **PYTORCH_TUNABLEOP_TUNING=1 required for Qwen3.6 compatibility.**
    Reddit/r/LocalLLM confirmed: Qwen3.5 configs work with Qwen3.6 when
    this flag is set. It auto-tunes CuBLAS GEMM kernels for the specific
    GPU architecture. Add as Docker env var: `-e PYTORCH_TUNABLEOP_TUNING=1`.
    Monitoring: After first few requests, CPU usage drops as tuning completes.
    Warm-up: initial requests may be slightly slower during auto-tuning.
    Source: r/LocalLLaMA + r/LocalLLM ROCm threads

65. **MTP SPECULATIVE DECODING DEGRADES Qwen3.6 by 62.5% (vLLM bug).**
    vLLM GitHub #38182 + #39680: Despite 96.6% acceptance rate, MTP causes
    generation throughput to DROP 62.5%. Root cause: KV cache manager
    force-drops the last matched block when MTP is enabled, collapsing
    prefix cache hit rate from 92% to 71%. This makes MTP counterproductive
    for Qwen3.5/3.6 on vLLM until the fix is merged.
    The block-dropping happens at:
    vllm/v1/core/single_type_kv_cache_manager.py#L457
    Combined with Qwen3.6's large block sizes (>1024), the impact is
    catastrophic. FIX: Comment out --speculative-config lines. RE-ENABLE
    when vLLM merges fix for #38182.
    Source: github.com/vllm-project/vllm/issues/38182 and #39680

66. **DavidAU "Why Abliterated Models SUCK" validates Restore SFT approach.**
    r/LocalLLaMA post + DavidAU Qwen3 TOTAL RECALL models confirm:
    abliteration damages MoE shared+nested expert representations, degrading
    performance especially on newer MoE models. DavidAU's "TOTAL RECALL v2"
    approach mirrors our Restore SFT pipeline: abliterate first, then
    targeted re-training with low LR to restore damaged capabilities.
    This validates our Phase 1 (Restore SFT) before Phase 3 (Generic SFT).
    NOT a code change — confirms our methodology is correct.
    Source: r/LocalLLaMA/comments/1nq0cp9 + huggingface.co/DavidAU

## NOT Applicable to DGX Spark (correctly rejected):

- **Hot Expert Caching** (ParmesanParty/llama.cpp fork): Caches frequently-
  routed MoE experts in VRAM. 27% faster for discrete GPU+CPU systems.
  NOT applicable: DGX Spark's UMA has zero PCIe bottleneck — all experts
  already in unified memory pool.

- **ik_llama.cpp** (custom-compiled backend): 70 tok/s on Qwen3.5-35B-A3B,
  5.53x faster than stock llama.cpp. NOT applicable: vLLM (120+ tok/s FP8)
  already faster. ik_llama.cpp excels for CPU-only/budget GPU setups.

- **--n-cpu-moe flag** (llama.cpp): 79 tok/s on RTX 5070 Ti with 128K context.
  NOT applicable: Solves PCIe bottleneck that UMA eliminates.

- **NVFP4/MXFP4 Quantization**: 20% faster than AWQ on DGX Spark per community.
  DEFERRED: BF16 training + FP8 serving already fits. Worth reconsidering
  for 122B+ model where VRAM is tight.
