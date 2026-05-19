# self-guide-internal-reward-rl-agents

*Researched: 2026-04-11 09:59 CDT*

# Self-Guide: Co-Evolution of Policy and Internal Reward for Language Agents

**Paper:** arXiv:2604.03098v1 (April 2026) — Wang et al., McGill/Mila/HKUST

## Core Innovation
Self-Guide is a self-generated internal reward for LLM agents that works at BOTH inference time (guidance) and training time (reward). The agent produces a short self-guidance signal on the current trajectory prefix, uses it to steer the next action during inference, and converts the same signal into step-level internal reward for denser policy optimization during training.

## Key Mechanism
1. **Inference-time:** Agent generates self-guidance signal → uses it to guide next action
2. **Training-time:** Same signal → step-level internal reward → denser GRPO optimization
3. **Co-evolution loop:** Better policy → better guidance → better internal reward → better policy

## Stage-Wise Trust Schedule (Critical for Stability)
- **Phase I:** Guidance-only warm-up (no reward)
- **Phase II:** Reward activation (gradual)
- **Phase III:** Full internal reward
- **Phase IV:** Late annealing (reduce internal reward weight)

This prevents immature self-judgments from destabilizing early training.

## Results
- 8% average improvement over GRPO on ALFWorld, ScienceWorld, WebShop
- Works with Qwen3-4B (small model, shows scalability)
- Offline-distilled self-guidance does NOT transfer reliably → must co-evolve online

## Relevance to Hermes Agent
- Hermes could implement self-guidance at inference: before each tool call, generate a brief "what should I do next" signal
- The same signal could be logged and used as step-level reward in Atropos training
- Stage-wise trust schedule directly applicable to Atropos environments
- Co-evolution principle: don't freeze the reward model, let it evolve with the policy

## Related: Group-in-Group Policy Optimization (GiGPO)
NeurIPS 2025 poster — extends GRPO from single-turn to multi-turn agent tasks. Addresses that GRPO's group-based advantage estimation breaks down in sequential decision-making.


## Sources

- https://arxiv.org/html/2604.03098v1
- https://neurips.cc/virtual/2025/poster/118123
