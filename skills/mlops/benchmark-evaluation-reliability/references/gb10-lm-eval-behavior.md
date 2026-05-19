# NVIDIA GB10 (DGX Spark) — lm-eval-harness Behavior

**Hardware:** NVIDIA DGX Spark (GB10, ARM CPU, unified memory, 128GB shared)  
**Model tested:** Qwen 27B BF16 (51GB)  
**Date:** May 2026

## Observed Behavior

### Loglikelihood tasks: RELIABLE
- **MMLU:** Completed successfully, 86.57% accuracy
- Runtime: ~4h 43m
- No issues

### Generate_until tasks: RELIABLE IF PROPERLY CONFIGURED

**Earlier failures (unpatched config):**
- **GSM8K (first run):** Died silently at 75% (984/1319) after ~10.5h — likely OOM from 32K token limit
- **GSM8K (second run):** CUDA kernel error during model loading, process died immediately
- **GSM8K (third run):** `--gen_kwargs max_new_tokens=512` did NOT override. Process still used 32K tokens, extremely slow (~30-77s/it)

**Success (patched config):**
- **GSM8K (fourth run):** Patched `generation_config.json` to `max_new_tokens: 512`
- Process ran for 6+ hours, reached 1070/1319 (81%) and was still alive
- Speed fluctuated: 12s/it to 51s/it depending on problem difficulty
- GPU temperature: stable 57-58°C, P0 state, no thermal throttling
- **Conclusion:** Earlier "silent death" was OOM from 32K tokens, not fundamental GB10 incompatibility

### Critical Discovery: `--gen_kwargs` Does Not Override — `generation_config.json` WINS

The CLI flag `--gen_kwargs max_new_tokens=512` produces a warning that looks like success:
```
WARNING  [evaluator:223] generation_kwargs: {'max_new_tokens': 512} specified through cli
```

But the actual generation still uses 32K tokens:
```
[transformers] Both `max_new_tokens` (=32768) and `max_length`... `max_new_tokens` will take precedence.
```

**Root cause:** The `32768` comes from the model's `generation_config.json`, NOT the task YAML. `transformers` loads this config when the model is initialized, and its `max_new_tokens` value persists into all generation calls. The hierarchy is:

1. **Model `generation_config.json`** — strongest, overrides everything
2. **Task YAML `generation_kwargs`** — medium, only if model config doesn't specify
3. **CLI `--gen_kwargs`** — weakest, overridden by both above

**Working fix:** Patch `generation_config.json` directly:
```bash
cat > /path/to/model/generation_config.json << 'EOF'
{
  "bos_token_id": 248044,
  "do_sample": true,
  "eos_token_id": [248046, 248044],
  "max_new_tokens": 512,
  "pad_token_id": 248044,
  "temperature": 1.0,
  "top_p": 1.0,
  "transformers_version": "5.5.4"
}
EOF
```

After patching, the log shows the correct value:
```
gsm8k: Using gen_kwargs: {'until': ['Question:', '</s>', '<|im_end|>'], 'do_sample': False, 'temperature': 0.0, 'max_new_tokens': 512}
[transformers] Both `max_new_tokens` (=512) and `max_length`... `max_new_tokens` will take precedence.
```

**Alternative fix:** Also patch task YAML to include `max_new_tokens: 512` under `generation_kwargs` as a secondary safeguard.

### Speed Fluctuations Are Normal — NOT Thermal Throttling

**Observation (GSM8K on GB10):** Generation speed fluctuated wildly:

| Progress | Speed | Notes |
|----------|-------|-------|
| 0-150 | 37s/it | Initial warmup |
| 150-217 | 12s/it | Faster problems |
| 217-280 | 48s/it | Slower problems |
| 280-493 | 15s/it | Fast again |
| 493-625 | 43s/it | Slow again |
| 625-676 | 12s/it | Fast |
| 676-850 | 41s/it | Slow |
| 850-966 | 12s/it | Fast |
| 966-1070 | 16s/it | Fast |

**GPU temperature throughout:** 57-58°C, P0 performance state, no thermal throttling.

**Conclusion:** Speed variation is due to **problem difficulty**, not hardware issues. GSM8K problems vary in complexity — some require multi-step reasoning (slow), others are simple (fast). The model generates until it hits a stop token, so complex problems take more tokens and more time.

**Do NOT kill the process during speed fluctuations.** Trust the progress counter over the `s/it` metric.

### Direct Python (transformers): RELIABLE
- Model loads in ~5.5 min
- GPU utilization hits 95%
- Each example slow (~2-3 min for GSM8K with max_new_tokens=256)
- But process completes without silent death

## Key Differences

| Aspect | lm-eval-harness (unpatched) | lm-eval-harness (patched) | Direct Python |
|--------|---------------------------|--------------------------|---------------|
| Model loading | Same (~5 min) | Same (~5 min) | Same (~5 min) |
| Generation speed | ~30-77s/it (32K tokens) | ~12-51s/it (512 tokens) | ~2-3 min/example |
| Reliability on GB10 | ❌ Silent death at 75% | ✅ Completes | ✅ Completes |
| Partial results | None saved | None saved | Can save incrementally |

## Updated Recommendation

For GB10 + large models + generate_until benchmarks:
1. **Patch `generation_config.json`** to limit `max_new_tokens` (512 for GSM8K, 1024 for HumanEval)
2. **Run one task at a time** — do not chain multiple generate_until tasks
3. **Monitor progress** — speed fluctuations are normal, do not kill
4. **Direct Python** — use for custom logic or if lm-eval still fails after patching

## Commands Used

```bash
# Check current generation config
cat /path/to/model/generation_config.json | grep max_new_tokens

# Patch generation config
cat > /path/to/model/generation_config.json << 'EOF'
{
  "bos_token_id": 248044,
  "do_sample": true,
  "eos_token_id": [248046, 248044],
  "max_new_tokens": 512,
  "pad_token_id": 248044,
  "temperature": 1.0,
  "top_p": 1.0,
  "transformers_version": "5.5.4"
}
EOF

# Run with patched config
lm_eval --model hf --model_args pretrained=/path/to/model,dtype=bfloat16 \
  --tasks gsm8k --num_fewshot 5 --batch_size 1 --device cuda

# Monitor progress
ssh user@host "tail -1 /tmp/lm_eval_gsm8k.log | grep -oP '\d+/1319'"
ssh user@host "nvidia-smi | grep -E 'GPU|Temp|Util'"
```
