# GR3-and-GRPO-plus-plus-RL-advances-2026

*Researched: 2026-04-10 01:32 CDT*

# RL Training Advances: GR³ and GRPO++ (2026)

## GR³: Group Relative Reward Rescaling (arxiv 2603.10535, Mar 2026)

**Problem:** Length inflation in RL-trained LLMs — models produce unnecessarily long trajectories to maximize rewards without proportional quality gains. Occurs in both RLHF (verbosity bias in reward models) and RLVR (inefficient reasoning chains).

**Key innovation:** Reframes length control as **multiplicative rescaling** rather than additive penalties. Additive penalties (R' = R - λℓ) create decoupled incentives where extreme brevity becomes a shortcut independent of task success. GR³ uses:
1. **Multiplicative Reward Rescaling** — continuous, reward-dependent gating mechanism
2. **Group-Relative Length Regularization** — adapts length budgets to instance difficulty
3. **Advantage-Aware Calibration** — preserves advantage signal of high-quality trajectories

**Results:** Maintains training dynamics comparable to standard GRPO while significantly mitigating length inflation. Outperforms state-of-the-art length-regularized baselines across RLHF and RLVR. Tested on DeepSeek-R1-Distill-7B.

**Implication for agent training:** When using GRPO for tool-calling RL environments, length inflation means agents learn to produce verbose tool-call sequences. GR³'s multiplicative approach could produce more concise, efficient tool-use patterns.

## GRPO++: Practical Tricks for RL at Scale (Cameron Wolfe, Jan 2026)

**Key insights from the deep dive:**

1. **Vanilla GRPO has subtle issues at scale** — the algorithm's conceptual simplicity masks practical pitfalls
2. **RLVR vs RLHF:** Most reasoning models use RLVR (verifiable rewards from ground truth) rather than RLHF (reward model from preferences)
3. **Verification matters more than expected:** Using LLM judges for math verification yields higher-quality models than strict parsing engines
4. **Inference scaling = reasoning ability:** Longer thinking chains improve performance, but need to be efficient (connects to GR³'s length work)

**Practical recommendations:**
- Math verification should use LLM judges, not just string matching
- RL training needs careful hyperparameter tuning — GRPO w/ KL-Cov is highly sensitive to optimization settings
- Reward miscalibration is a significant issue in agentic RL tasks (separate OpenReview paper)
- Need to distinguish between "productive reasoning length" and "inflation"

## Cross-Domain Synthesis

**GR³ × Agent Tool-Calling:** The multiplicative reward rescaling paradigm could directly improve RL environments for training tool-calling agents. Current GRPO-based environments (like Hermes Atropos environments) could benefit from GR³'s approach to prevent agents from learning unnecessarily verbose multi-step strategies when simpler ones suffice.

**Verification → Agent Evaluation:** The insight that LLM judges outperform strict parsers for verification suggests that agent evaluation metrics should use semantic equivalence checking rather than exact match on tool outputs.


## Sources

- https://arxiv.org/html/2603.10535v1
- https://cameronrwolfe.substack.com/p/grpo-tricks
