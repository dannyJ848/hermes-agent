# qwen27b-benchmark-evaluation-may2026

*Researched: 2026-05-11 00:06 CDT*

# Qwen 27B Expert Logician — Benchmark Evaluation (In Progress)

## Model
- **Base**: Qwen3.6-27B-Uncensored
- **Training**: LoRA r=256, alpha=512 + SAE + teacher distillation
- **Steps**: 10,000 (completed May 10, 2026)
- **Merged Model**: /data/SpecForge/custom_dflash/checkpoints/final_model_merged/
- **Size**: 51GB (26.9B parameters, BF16)
- **Hardware**: DGX Spark (NVIDIA GB10, Blackwell)

## Results So Far

### Direct Reasoning Tests (Custom)
| Test | Score |
|------|-------|
| Wason Selection | 100% |
| Syllogism Barbara | 100% |
| Math Proof (sqrt(2)) | 75% |
| Counterfactual | 67% |
| Ambiguous Premise | 33%* |
| Edge Case (0.999...=1) | 100% |
| **Average** | **79.2%** |

*Scored low on keyword matching; reasoning was actually correct

### MMLU (lm-eval-harness) — COMPLETE
| Category | Score |
|----------|-------|
| **Overall** | **86.57%** |
| Humanities | 82.27% |
| STEM | 85.98% |
| Social Sciences | 91.91% |
| Other | 88.38% |

**Runtime**: ~4h 43m (56,168 loglikelihood requests)

### In Progress
- **GSM8K**: Running (PID 3233497, started 23:56 CDT)
- **HumanEval**: Queued
- **BBH**: Queued
- **ARC Challenge**: Queued
- **WinoGrande**: Queued

## Key Files
- MMLU Results: `/data/SpecForge/custom_dflash/evaluation_results/mmlu_full/`
- Benchmark Log: `/data/SpecForge/custom_dflash/evaluation_results/benchmark_suite.log`
- Distillation: `/data/SpecForge/custom_dflash/BENCHMARK_DISTILLATION.md`
- Direct Eval: `/data/SpecForge/custom_dflash/evaluation_results/direct_evaluation.json`

## Resume Instructions
```bash
# Check progress
ssh djg6228@10.0.0.171 "ps aux | grep lm_eval; tail -20 /data/SpecForge/custom_dflash/evaluation_results/benchmark_suite.log"

# Get results when complete
ls /data/SpecForge/custom_dflash/evaluation_results/*/
```

## Observations
- lm-eval-harness on GB10: starts slow (~1.1s/it) but warms up to ~7.3 it/s
- Model reloads between benchmarks (~5 min each)
- GPU temp peaks at 80°C, cools to 53°C between runs
- Background SSH process survives disconnects
- System RAM: 121GB total, 102GB used during model load

## Next Steps
1. Monitor GSM8K completion
2. Collect HumanEval, BBH, ARC, WinoGrande results
3. Compile final comprehensive report
4. Deploy with vLLM for inference serving

---
*Distilled: May 10, 2026 23:57 CDT*
*Checkpoint: qwen27b-benchmarks-in-progress-may10*
