# vllm-dgx-qwen36-optimization

*Researched: 2026-05-15 11:49 CDT*

# vLLM DGX Qwen3.6-27B Optimization Report

## Executive Summary

Successfully optimized Qwen3.6-27B-Uncensored inference on DGX Spark from 6.6 tok/s to **18.4 tok/s** (2.8x speedup) using DFlash speculative decoding with zero quality degradation.

## Tested Configurations

### Baseline (Original)
- Prefix caching: ON
- Batch tokens: 8192
- Speculative: n-gram (5 tokens)
- **Throughput: 6.6 tok/s**

### Config A (Tuning)
- Prefix caching: OFF (Mamba incompatibility)
- Batch tokens: 32768
- Max seqs: 128
- Speculative: n-gram (5 tokens)
- **Throughput: 6.5 tok/s** (-1%, but cleaner logs)

### Config B (Native MTP)
- Attempted to use model's built-in MTP weights
- FAILED: vLLM 0.20.2 requires `model_type="qwen3_5_mtp"` for auto-detection
- Checkpoint has `model_type="qwen3_5"` with `mtp_num_hidden_layers=1`
- Weight initialization errors when forcing draft_model method

### Config C (DFlash)
- Draft model: Qwen3.5-27B-DFlash (3.3GB, 5 layers)
- Speculative tokens: 16
- **Throughput: 18.4 tok/s** (+179%)
- Acceptance rate: 24.2% average
- **Quality: No degradation**

## Key Findings

1. **DFlash is the winner**: 2.8x speedup with lossless quality
2. **Qwen3.6-27B-DFlash is GATED**: Cannot download without HF access approval
3. **Qwen3.5-27B-DFlash works as fallback**: Compatible with Qwen3.6-27B main model
4. **Native MTP not viable**: Checkpoint format mismatch prevents vLLM auto-detection
5. **Prefix caching broken for Mamba**: 0% hit rate, causes log spam

## Trade-offs

| Metric | Baseline | DFlash | Impact |
|--------|----------|--------|--------|
| Throughput | 6.6 tok/s | 18.4 tok/s | +179% ✅ |
| KV cache | 966K tokens | 499K tokens | -48% ⚠️ |
| Max concurrency | 7.4x | 3.8x | -49% ⚠️ |
| Quality | Baseline | Identical | No change ✅ |

## Production Deploy Script

File: `/tmp/deploy_vllm_dflash.sh`

```bash
docker run -d \
  --name vllm-merged \
  --runtime nvidia \
  --gpus all \
  -p 8000:8000 \
  -v /data:/data \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --enable-chunked-prefill \
  --speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":16}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 128
```

## Future Work

1. **EAGLE-3**: Test if EAGLE-3 draft models give better acceptance rates
2. **FP8 KV cache**: When vLLM supports it for this model
3. **vLLM upgrade**: Newer versions may have better MTP support
4. **Qwen3.7**: Expected higher performance when released

## Files

- `/tmp/deploy_vllm_dflash.sh` — Production deploy script
- `/tmp/benchmark_vllm.py` — Benchmark script
- `/tmp/vllm_optimization_results.json` — Complete results
- `/data/models/Qwen3.5-27B-DFlash/` — Draft model (3.3GB)


## Sources

- https://github.com/z-lab/dflash
- https://huggingface.co/z-lab/Qwen3.5-27B-DFlash
- https://huggingface.co/z-lab/Qwen3.6-27B-DFlash
