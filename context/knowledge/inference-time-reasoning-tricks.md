# inference-time-reasoning-tricks

*Researched: 2026-04-20 05:47 CDT*

# Bag of Tricks for Inference-time LLM Reasoning

**Source:** NeurIPS 2025, Liu et al. (HKUST)

Key findings from 1000+ experiments, 20,000+ A100 GPU hours:

1. **Temperature 0.8 + Top-p 0.9** is optimal baseline for reasoning (2-5% improvement)
2. **Self-correction/reflection often fails** — standard CoT more reliable
3. **Process rewards** (evaluating steps) outperform outcome rewards for math/code
4. **Self-Consistency** (majority voting) is most token-efficient inference scaling
5. **Tricks are NOT additive** — combining doesn't compound gains

## Hermes Implications
- Process-based evaluation of tool chains > final output only
- Self-Consistency for delegation: delegate 3x, pick consensus answer
- Default to Temperature 0.8 / Top-p 0.9 for reasoning-heavy tasks

## Sources

- https://neurips.cc/virtual/2025/poster/121550
- https://github.com/usail-hkust/benchmark_inference_time_computation_LLM
