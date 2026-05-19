# Post-Training Evaluation on DGX Spark GB10 — May 2026 Findings

## Verified Evaluation Results (Qwen 27B BF16)

| Benchmark | Score | Runtime | Reliability |
|-----------|-------|---------|-------------|
| MMLU | **86.57%** | ~4h 43m | ✅ Reliable (loglikelihood) |
| GSM8K | **66.19%** strict | ~12h | ✅ Reliable with patch |
| HumanEval | **82.93%** pass@1 | ~44m | ✅ Reliable with flags |

### MMLU Breakdown
- Humanities: 82.27%
- STEM: 85.98%
- Social Sciences: 91.91%
- Other: 88.38%

## Critical: `generation_config.json` Patch for Generate_Until Tasks

**Without patch:** Default `max_new_tokens: 32768` causes:
- Extreme slowdown (effectively hangs)
- OOM on unified memory
- Silent death at 75%+ completion

**Patch:**
```bash
python3 -c "
import json
with open('/data/SpecForge/custom_dflash/checkpoints/final_model_merged/generation_config.json', 'r') as f:
    config = json.load(f)
config['max_new_tokens'] = 512
with open('/data/SpecForge/custom_dflash/checkpoints/final_model_merged/generation_config.json', 'w') as f:
    json.dump(config, f, indent=2)
"
```

**Why 512?** GSM8K and HumanEval answers are short (<100 tokens). 512 is generous.

## HumanEval Requires Two Flags

```bash
export HF_ALLOW_CODE_EVAL=1
lm_eval --tasks humaneval --confirm_run_unsafe_code ...
```

Missing either = immediate death with `ValueError: Attempted to run task: humaneval which is marked as unsafe.`

## Speed Fluctuations Are Normal

GSM8K varied from 12s/it to 58s/it. GPU temp stayed at 57-58°C. This is **problem difficulty variation**, NOT thermal throttling. Do NOT kill process during slowdowns.

## Model Loading Time

Qwen 27B BF16 loads in ~5.5 minutes on GB10. Process may appear "dead" during loading — verify with `ps` before declaring failure.

## Recommended Evaluation Sequence

1. Patch `generation_config.json` first (one-time)
2. Run MMLU (loglikelihood, reliable, ~5h)
3. Run GSM8K (generate_until, ~12h with patch)
4. Run HumanEval (generate_until, ~45m, needs flags)
5. Run BBH (generate_until, long — consider vLLM API instead)

## Backend Recommendation for GB10

| Task Type | Backend | Reliability |
|-----------|---------|-------------|
| Loglikelihood (MMLU, ARC, WinoGrande) | lm-eval-harness | ✅ High |
| Generate_until (GSM8K, HumanEval) | lm-eval-harness + patch | ✅ Medium-High |
| Generate_until (BBH — 6511 examples) | vLLM API or direct Python | ⚠️ Consider faster backend |

BBH at 6511 examples with ~24s/it = ~43 hours. For long benchmarks, consider vLLM API for 5-10x speedup.
