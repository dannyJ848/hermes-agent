# rl-training-grpo-gigpo-2026

*Researched: 2026-04-10 00:02 CDT*

# RL Training Advances for LLM Agents (April 2026)

## Key Discoveries

### 1. GiGPO — Group-in-Group Policy Optimization (NeurIPS 2025)
- **Problem:** GRPO struggles with credit assignment in long-horizon multi-turn agent tasks
- **Solution:** Hierarchical grouping — groups within groups for fine-grained credit assignment
- **Key insight:** Single-turn GRPO improvement provides a lower bound for multi-turn success
- **Source:** openreview.net/forum?id=QXEhBMNrCW

### 2. Flow-GRPO Survey (arXiv 2603.06623)
- **Massive survey** covering all GRPO variants for generative models
- **7 dimensions of improvement:** reward signal design, credit assignment, sampling efficiency, diversity preservation, reward hacking mitigation, ODE vs SDE sampling, reward model design
- **Key variants:** DenseGRPO (step-level rewards), TreeGRPO (tree search), E-GRPO (entropy-driven), DiverseGRPO (mode collapse prevention), GRPO-Guard (reward hacking)
- **Applied to:** T2I, video, 3D, speech, VLA/embodied AI, unified multimodal

### 3. verl — Volcano Engine RL Library (GitHub 20.6k stars)
- **Production-grade** RL training library for LLMs
- Supports GRPO, PPO in a few lines of code
- Modular APIs decoupling computation and data flow
- Active development: 2,334 commits, 3.6k forks

### 4. Multi-turn Task Reasoning (MERL TR2026-026)
- Theoretical analysis connecting single-turn GRPO gains to multi-turn agent success
- **Lower bound proof:** GRPO improvement on single-turn reasoning → multi-turn performance guarantee
- Critical for agent training: validates that single-turn RL training transfers to multi-turn scenarios

## Implications for Hermes Agent
1. **GiGPO** could improve Atropos environment credit assignment for agent RL training
2. **DenseGRPO** (step-level rewards) maps to tool-call-level reward shaping for agent fine-tuning
3. **verl** is the go-to framework for implementing GRPO/Atropos training pipelines
4. **Reward hacking mitigation** (GRPO-Guard, GARDO) essential for preventing agent reward gaming

## Sources
- arxiv.org/html/2603.06623v1
- openreview.net/forum?id=QXEhBMNrCW
- github.com/verl-project/verl
- cameronrwolfe.substack.com/p/grpo
- merl.com/publications/docs/TR2026-026.pdf


## Sources

- https://arxiv.org/html/2603.06623v1
- https://openreview.net/forum?id=QXEhBMNrCW
- https://github.com/verl-project/verl
- https://cameronrwolfe.substack.com/p/grpo
- https://www.merl.com/publications/docs/TR2026-026.pdf
