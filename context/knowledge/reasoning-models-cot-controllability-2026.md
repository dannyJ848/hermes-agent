# reasoning-models-cot-controllability-2026

*Researched: 2026-04-15 00:23 CDT*

# Reasoning Models: CoT Controllability & The Illusion of Thinking

## Paper 1: Reasoning Models Struggle to Control their Chains of Thought (arXiv 2603.05706, Mar 2026)
- **Authors:** Chen Yueh-Han (NYU/MATS), Robert McCarthy (UCL/MATS), Bruce W. Lee (UPenn/MATS), He He (NYU), OpenAI team
- **Key finding:** Reasoning models have significantly lower CoT controllability than output controllability. Claude Sonnet 4.5 controls CoT only 2.7% of the time vs 61.9% for output control.
- **CoT controllability increases with parameter count** but **decreases with more RL training, test-time compute, and problem difficulty**.
- **Implication for agent safety:** CoT monitoring remains a viable oversight mechanism because models can't easily hide their reasoning. However, the mechanism is not well understood.
- **Benchmark:** CoT-Control evaluation suite available at github.com/YuehHanChen/CoTControl

## Paper 2: The Illusion of Thinking (Apple ML Research, NeurIPS 2025)
- **Authors:** Parshin Shojaee, Iman Mirzadeh, et al.
- **Key finding:** LRMs (Large Reasoning Models) face **complete accuracy collapse beyond certain complexity thresholds**.
- **Counter-intuitive scaling limit:** Reasoning effort increases with complexity up to a point, then *declines* despite adequate token budget.
- **Three performance regimes:**
  1. Low complexity: standard LLMs *outperform* LRMs (overthinking)
  2. Medium complexity: LRMs show advantage from extended thinking
  3. High complexity: both collapse completely
- **LRMs fail to use explicit algorithms** and reason inconsistently across puzzles.
- **Implication for agent systems:** Simple CoT doesn't scale to complex multi-step reasoning. Need external tool use, verified computation, and structured decomposition.

## Agent Design Implications
1. CoT monitoring is reliable for safety oversight (low controllability = high monitorability)
2. For complex tasks, pure CoT reasoning will fail — must decompose into verified sub-steps
3. Over-reasoning on simple tasks wastes compute — need adaptive reasoning depth
4. RL training paradoxically reduces CoT controllability while improving performance


## Sources

- https://arxiv.org/html/2603.05706v1
- https://machinelearning.apple.com/research/illusion-of-thinking
