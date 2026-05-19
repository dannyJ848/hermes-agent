# policy-of-thoughts-test-time-reasoning

*Researched: 2026-04-13 08:29 CDT*

# Policy of Thoughts (PoT): Test-Time Policy Evolution for LLM Reasoning

**Paper:** arXiv 2601.20379 (2025)
**Authors:** Jiao et al. (Zhejiang University, LMU Munich)

## Key Innovation
Recasts LLM reasoning as **within-instance online optimization** rather than post-hoc trajectory filtering. Inspired by Popper's "conjectures and refutations" epistemology.

## How It Works
1. **Exploration Phase**: Uses MCTS to generate diverse candidate solution trajectories
2. **Policy Internalization**: Applies GRPO (Group Relative Policy Optimization) to update a **transient LoRA adapter** based on execution feedback
3. **Closed-Loop**: The model's reasoning priors are refined per-instance before committing to a final answer

## Why It Matters
- Existing test-time scaling (Best-of-N, Reflexion, Tree of Thoughts) treats feedback as external selection signal — they discard failed trajectories without learning from them
- PoT **internalizes failures** via gradient updates, enabling real-time reasoning policy evolution
- A 4B parameter model achieves **49.71% on LiveCodeBench**, outperforming GPT-4o and DeepSeek-V3 despite being 50x smaller

## Agent Design Implications
- **For Hermes:** The transient LoRA concept could apply to agent tool-selection — adapt the policy per-task rather than using static routing
- **Relevance to distillation:** Tips should capture not just what works but what failed and why (credit assignment loop)
- **Connection to aggressive_continue:** The "frozen policy" problem mirrors why fixed prompt rules fail — the agent needs to evolve its strategy mid-session

## Baselines Outperformed
Simple CoT, Few-shot, Best-of-N, Reflexion, Self-Refine, ToT, LDB, RAP, LATS, AB-MCTS, RethinkMCTS, CodeT


## Sources

- https://arxiv.org/html/2601.20379v1
