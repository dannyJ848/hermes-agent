# reasoning-test-time-optimization-2026

*Researched: 2026-04-20 13:00 CDT*

# Test-Time Reasoning Optimization Advances (2026)

**Date:** 2026-04-20
**Domain:** REASONING

## ∇-Reasoner: Test-Time Gradient Descent in Latent Space

**Paper:** arXiv:2603.04948 (ICLR 2026)
**Authors:** Peihao Wang, Ruisi Cai, Zhen Wang, Hongyuan Mei, Qiang Liu, Pan Li, Zhangyang Wang

### Core Innovation
Moves beyond discrete search (zeroth-order) to **first-order optimization at test time** via gradient descent over token logits during decoding.

### Key Components
- **Differentiable Textual Optimization (DTO):** Uses gradients from both LLM likelihood and reward model to refine textual representations during generation
- **Rejection Sampling:** Robustifies decoding
- **Acceleration Design:** Speeds up decoding

### Results
- **>20% accuracy improvement** on challenging math reasoning benchmarks
- **~10-40% reduction** in model calls vs. strong baselines

### Theoretical Insight
Inference-time gradient descent in sample space to maximize reward is **dual to KL-regularized RL alignment**.

---

## Re²: Reinforcement Learning with Re-solving

**Paper:** arXiv:2603.07197 (ICLR 2026)
**Authors:** Pinzheng Wang, Shuli Xu, Juntao Li, Yu Luo, Dong Li, Jianye Hao, Min Zhang

### Problem
Standard RLVR models generate unnecessary/low-quality CoT steps, leading to **inefficient overthinking** and lower answer quality.

### Solution
**Pure RL approach** (no SFT) where models learn to **abandon unproductive reasoning paths and restart** when necessary.

### Results
- Redo behavior amplified from **0.5% → >30%**
- Substantial gains over standard RLVR at **same compute budget**
- Benefits compound with increased test-time sampling

### Why It Matters
- Eliminates overthinking waste
- Self-correction from poor initial CoT directions
- Better test-time compute allocation

---

## Implications for Agent Systems

1. **∇-Reasoner** could optimize tool-call planning by applying gradient descent over tool selection logits
2. **Re²** style re-solving could help agents backtrack from failed tool sequences instead of continuing down broken paths
3. Both techniques suggest inference-time scaling is moving from "more samples" to "smarter optimization"

## Sources
- https://arxiv.org/abs/2603.04948
- https://arxiv.org/abs/2603.07197


## Sources

- https://arxiv.org/abs/2603.04948
- https://arxiv.org/abs/2603.07197
