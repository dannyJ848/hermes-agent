# DFlash Speculative Decoding Optimization Notes
## Session: May 16, 2026

## Key Finding: num_speculative_tokens Sweet Spot

From NVIDIA forums and HuggingFace discussions on Qwen3.5-27B-DFlash:

| num_speculative_tokens | Acceptance Rate | Speed | Notes |
|------------------------|----------------|-------|-------|
| 15 | ~12% | Variable, sometimes slower | Default recommendation, but poor acceptance |
| **8** | **25-30%** | **Optimal** | **Sweet spot for Qwen3.5 27B** |
| 5 | ~20% | Baseline | Conservative |

**Rule of thumb**: Lower num_speculative_tokens improves acceptance rate up to a point. For Qwen3.5 27B with DFlash, 8 is the sweet spot.

## vLLM + Dynamic LoRA + Speculative Decoding: Known Issues

- **GitHub Issue #6912**: "Reduce LoRA latency via speculative decoding" — CLOSED as not planned
  - vLLM speculative decoding framework allows target model to have LoRAs, but batch expansion for LoRA was never implemented
- **Performance penalty**: 10-20% overhead from cudagraph_specialize_lora even when LoRA not used
- **First request penalty**: 1-2 minutes for initial LoRA loading/optimization
- **Eager mode fallback**: When sequence > --max-seq-len-to-capture (default 8192), falls back to eager mode (much slower)
- **Fix**: Set --max-seq-len-to-capture to match max_model_len (e.g., 131072)

## Alternative Inference Servers

| Server | LoRA Support | Speculative Decoding | Speed vs vLLM | Notes |
|--------|-------------|---------------------|---------------|-------|
| **SGLang** | ✅ Dynamic (S-LoRA/Punica) | ✅ EAGLE-2/EAGLE-3/MTP/DFLASH | **+29% throughput** | **Best alternative** |
| vLLM | ✅ Dynamic | ✅ DFlash/EAGLE/MTP | Baseline | LoRA + spec decode has issues |
| TGI | ✅ | ✅ | Slower | HuggingFace ecosystem |
| TensorRT-LLM | ❌ Static only | ✅ | Fastest | NVIDIA-only, no dynamic LoRA |

## SGLang Advantages for LoRA + Speculative

- S-LoRA + Punica for efficient multi-LoRA batching
- RadixAttention for automatic prefix caching
- 29% higher throughput than vLLM on H100
- 2x higher output throughput
- Better scheduling efficiency for multi-turn conversations

## Recommended Deployment

For vision model + dynamic LoRA + speculative decoding at 25%+ acceptance:

**Option A: SGLang (Recommended)**
- Deploy SGLang instead of vLLM
- Use S-LoRA for dynamic adapter loading
- EAGLE-3 or MTP for speculative decoding
- Expected: 20-30+ tok/s with 30-40% acceptance

**Option B: Optimize vLLM**
- Reduce num_speculative_tokens from 15 to 8
- Increase --max-seq-len-to-capture to 131072
- Use --enable-lora with --max-loras-per-batch 1
- Warm up LoRA before production traffic
- Expected: 10-15 tok/s with 25% acceptance

**Option C: Hybrid**
- Use merged text-only model for speed-critical tasks (65 tok/s)
- Use base + dynamic LoRA only when vision is needed
- Switch between them via Hermes config
