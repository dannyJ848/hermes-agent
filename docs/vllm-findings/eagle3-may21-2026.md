# vLLM EAGLE-3 Deep Dive Findings — May 21, 2026

## Session Summary

5+ hours of persistent debugging to get EAGLE-3 speculative decoding working on DGX Spark GB10 with Qwen3.6-27B-Uncensored BF16.

## Results

| Method | Speed | Acceptance | Status |
|--------|-------|-----------|--------|
| Baseline | 3.1 tps | N/A | Stable |
| MTP-5 | 5.4 tps | ~14% | **Best so far** |
| EAGLE-3 (specdrift) | 1.5 tps | ~5-8% | Misaligned drafter |

## Key Discoveries

### 1. EAGLE-3 Requires Custom-Trained Drafter
The `specdrift-qwen3.6-27b-eagle3` drafter (advertised as EAGLE-3 for Qwen3) gets only 0-13% acceptance (mostly 5-8%), making it 50% SLOWER than baseline. The drafter is severely misaligned with the target model's tokenizer and hidden states.

**Lesson**: Off-the-shelf EAGLE-3 drafters are NOT plug-and-play. They must be trained specifically for the target model.

### 2. vLLM 0.21.0 Speculative Config Format
```bash
vllm serve ... --speculative-config '{"method":"eagle3","model":"/path/to/drafter","num_speculative_tokens":5}'
```
Valid methods: `mtp`, `eagle3`, `ngram`, `suffix`

### 3. EAGLE-3 Patching Required
vLLM's `llama_eagle3.py` needs to skip `fcs.X.weight` tensors that specdrift models have but vLLM doesn't support:
```python
if "fcs." in name:
    continue
```

### 4. GB10-Specific Findings
- CUDA graph compilation is ESSENTIAL (300s startup vs 70s with --enforce-eager, but 3x faster inference)
- GB10 unified memory is memory-bandwidth bound
- Optimal config: `--max-num-batched-tokens 65536 --max-num-seqs 64 --gpu-memory-utilization 0.85 --enable-prefix-caching --max-model-len 65536`

## Files Modified on DGX
- `/data/SpecForge/venv/lib/python3.12/site-packages/vllm/model_executor/models/llama_eagle3.py` — patched to skip `fcs.` weights
- `/data/SpecForge/venv/lib/python3.12/site-packages/vllm/model_executor/models/qwen3_eagle3.py` — custom model (disabled, obsolete)
- `/data/SpecForge/venv/lib/python3.12/site-packages/vllm/model_executor/models/registry.py` — modified for Eagle3Qwen3ForCausalLM
- `/data/benchmarks/overnight_benchmark.py` — systematic benchmark runner
- `/data/benchmarks/eagle3_config.json` — EAGLE-3 speculative config

## Overnight Benchmark
Running at `/data/benchmarks/overnight_benchmark.py` — tests baseline + MTP-3/5/7/10 + ngram + suffix decoding. Results in `/data/benchmarks/overnight_results.json`.
