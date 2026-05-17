# test-time-compute-reasoning-scaling-2026

*Researched: 2026-04-14 15:55 CDT*

# Test-Time Compute Scaling for LLM Reasoning (2025-2026)

## Key Papers

### 1. Policy of Thoughts (PoT) — arXiv:2601.20379 (Jan 2026)
- **Core idea:** Recast reasoning as within-instance online optimization. Generate diverse candidate solutions, then use GRPO to update a transient LoRA adapter based on execution feedback.
- **Key result:** 4B parameter model achieves 49.71% on LiveCodeBench, outperforming GPT-4o and DeepSeek-V3 despite being 50x smaller.
- **Inspiration:** Popper's "conjectures and refutations" — intelligence requires real-time policy evolution from failed attempts.
- **Technical approach:**
  1. Efficient exploration mechanism generates diverse candidate solutions
  2. Execution feedback identifies failures
  3. GRPO (Group Relative Policy Optimization) updates transient LoRA adapter
  4. Instance-specific refinement of reasoning priors
- **Relevance to Hermes:** This is essentially what our distillation loop does at a coarser granularity. PoT does it per-instance. Could inform real-time self-correction patterns.

### 2. Forest-of-Thought (ICML 2025)
- Extends Chain-of-Thought and Tree-of-Thought with forest-level reasoning
- Scales test-time compute by exploring multiple reasoning paths simultaneously

### 3. Fine-Tuning vs Test-Time Compute (NeurIPS 2025)
- Examines the interaction between fine-tuning and test-time compute scaling
- Finding: there are limits to how much test-time compute can compensate for insufficient fine-tuning

## Synthesis for Agent Systems
- **Test-time compute scaling is the dominant paradigm for 2025-2026** reasoning improvements
- PoT's transient LoRA approach is architecturally similar to what Hermes could do with per-task skill adaptation
- The 4B > GPT-4o result suggests that targeted self-improvement at inference time can dramatically outperform raw scale
- For autonomous agents: the key insight is that execution feedback should be INTERNALIZED into reasoning strategy, not just used for filtering

## Sources

- https://arxiv.org/abs/2601.20379
- https://magazine.sebastianraschka.com/p/state-of-llms-2025
- https://icml.cc/virtual/2025/poster/46117
- https://neurips.cc/virtual/2025/poster/116423
