# rl-training-grpo-advances-2026

*Researched: 2026-04-10 13:16 CDT*

# GRPO Advances for LLM Agent Training (2025-2026 Survey)

## Key Papers

### 1. Flow-GRPO: Extending GRPO to Generation Models (arXiv 2603.06623)
- Flow-GRPO extends Group Relative Policy Optimization from LLMs to flow matching models (T2I, video, 3D, speech)
- **Methodological advances beyond original framework:**
  - **Reward signal design**: Sparse→Dense (DenseGRPO, SuperFlow step-level rewards)
  - **Credit assignment**: Trajectory→Step level (TreeGRPO, BranchGRPO, Chunk-GRPO, PCPO)
  - **Sampling efficiency**: E-GRPO (high-entropy step driven), MixGRPO (mixed ODE-SDE), Smart-GRPO
  - **Mode collapse prevention**: DiverseGRPO, OSCAR (orthogonal stochastic control), DRIFT
  - **Reward hacking mitigation**: GRPO-Guard, GARDO, DDRL, CPS
  - **ODE vs SDE strategies**: Neighbor GRPO, TAFS-GRPO (temperature-annealed)

### 2. Group-in-Group Policy Optimization for LLM Agent Training (NeurIPS 2025)
- Extends group-based RL from single-turn tasks to multi-turn agent training
- Addresses the gap between single-turn reasoning and multi-turn planning

### 3. Training Task Reasoning LLM Agents (MERL TR2026-026)
- GRPO improvement on single-turn reasoning provides a lower bound for multi-turn success
- Multi-turn task planning via RL-trained agents

## Key Insight for SOMA
The GRPO framework is evolving rapidly from single-turn to multi-turn agent training. The Group-in-Group approach and step-level credit assignment are directly applicable to training agents for medical tool use and multi-step diagnostic reasoning.


## Sources

- https://arxiv.org/html/2603.06623v1
- https://neurips.cc/virtual/2025/poster/118123
- https://www.merl.com/publications/docs/TR2026-026.pdf
