# Qwen 27B Expert Logician — Evaluation Results (May 10-11, 2026)

## Hardware
- DGX Spark (NVIDIA GB10, Blackwell)
- 121GB system RAM, ~128GB GPU VRAM
- Host: spark-85e8.local (10.0.0.171)

## Model
- Base: Qwen3.6-27B-Uncensored
- Training: LoRA r=256, alpha=512, 10,000 steps + SAE + teacher distillation
- Merged: May 10, 2026 at 17:35
- Size: 51GB BF16, 2 safetensor shards, 26.9B parameters
- Path: `/data/SpecForge/custom_dflash/checkpoints/final_model_merged/`

---

## Direct Reasoning Evaluation

Script: `qwen_direct_eval.py` (transformers + device_map="auto")
Load time: ~5 minutes
Inference: 6 tests, 200 tokens each, ~30 seconds total

| Test | Category | Score | Response Summary |
|------|----------|-------|-----------------|
| Wason Selection (drinking age) | Deductive Reasoning | **100%** | Correctly identified Beer + 16 years |
| Syllogism Barbara | Classical Logic | **100%** | Identified AAA-1 form, explained categorical syllogism |
| sqrt(2) Irrationality Proof | Mathematical Reasoning | **75%** | Correct contradiction structure, minor rigor gaps |
| Counterfactual Socrates | Modal Reasoning | **67%** | Correctly identified premise contradiction invalidates argument |
| Ambiguous Premise (rain) | Robustness | **33%** | *Actually correct* — identified "affirming the consequent" fallacy. Low score due to strict keyword matching (used LaTeX notation $P$, $Q$ not in expected keywords) |
| 0.999... = 1 Edge Case | Edge Case | **100%** | Correct, mentioned limit, geometric series, algebraic proof |

**Average: 79.2%**

---

## Standard Benchmarks — lm-eval-harness (FULL RUN)

**CRITICAL DISCOVERY**: lm-eval-harness IS viable on GB10 when run correctly via background SSH session. Previous attempts failed due to SSH timeout, not hardware limitation.

### Correct Execution Pattern

Use `terminal(background=true)` with a single SSH session that runs benchmarks sequentially:

```bash
ssh djg6228@10.0.0.171 "bash -c 'cd /data/SpecForge/custom_dflash && source eval_venv/bin/activate && lm_eval --model hf --model_args pretrained=/data/SpecForge/custom_dflash/checkpoints/final_model_merged,dtype=bfloat16 --tasks mmlu --num_fewshot 5 --batch_size 1 --output_path evaluation_results/mmlu_full --device cuda && lm_eval ... gsm8k ... && lm_eval ... humaneval ... && ...'"
```

**DO NOT use nohup in foreground SSH** — the terminal tool blocks shell-level background wrappers. The `terminal(background=true)` backgrounds the SSH session itself, which is the correct pattern.

### MMLU (COMPLETE)

| Metric | Value |
|--------|-------|
| Overall | **86.57%** |
| Humanities | 82.27% |
| Social Sciences | 91.91% |
| STEM | 85.98% |
| Other | 88.38% |
| Runtime | ~4h 43m |
| Speed | 3.3-7.3 it/s (improved after warmup) |

**Notable subtask scores** (from log tail):
- Computer Security: 86.00%
- Conceptual Physics: 94.47%
- Electrical Engineering: 86.21%
- Elementary Mathematics: 89.15%
- High School Biology: 94.84%
- High School Chemistry: 82.27%
- High School CS: 93.00%
- High School Mathematics: 70.74%
- High School Physics: 84.11%
- High School Statistics: 89.81%
- Machine Learning: 79.46%

### GSM8K (IN PROGRESS)

Started after MMLU completion. Running `generate_until` requests (more efficient than `loglikelihood`).

### Benchmark Suite Queue

1. ✅ MMLU — COMPLETE (86.57%)
2. 🔄 GSM8K — RUNNING
3. ⏳ HumanEval — queued
4. ⏳ BBH — queued
5. ⏳ ARC Challenge — queued
6. ⏳ WinoGrande — queued

---

## Key Findings (Updated)

1. **Model loads successfully on GB10** (5 min load, 95% GPU utilization)
2. **Direct evaluation is reliable and fast** for quick verification
3. **lm-eval-harness works on GB10 when run via background SSH session** — previous failures were SSH timeout, not hardware
4. **MMLU score of 86.57% is excellent** — well above base model expectations
5. **Speed improves dramatically after warmup** — starts at 1.1s/it, reaches 7.3 it/s by end
6. **Tokenizer files must be copied manually after merge**
7. **Use `terminal(background=true)` for long evaluations** — not nohup in foreground

---

## Files

- `/data/SpecForge/custom_dflash/evaluation_results/direct_evaluation.json`
- `/data/SpecForge/custom_dflash/evaluation_results/direct_evaluation.md`
- `/data/SpecForge/custom_dflash/evaluation_results/mmlu_full/` — MMLU results JSON
- `/data/SpecForge/custom_dflash/evaluation_results/benchmark_suite.log` — Full suite log
- `/data/SpecForge/custom_dflash/FINAL_EVALUATION_REPORT.md`
