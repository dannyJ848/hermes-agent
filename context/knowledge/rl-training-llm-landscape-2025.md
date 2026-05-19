# rl-training-llm-landscape-2025

*Researched: 2026-04-09 23:23 CDT*

# RL Training for LLMs — State of the Art (April 2025)

## Key Libraries

### Atropos (NousResearch)
- Fully sovereign RL framework for frontier LLM training
- Trajectory API server coordinates environment interactions
- Community environments growing (humor, math, coding)
- Integrated into Hermes Agent via `environments/` directory

### GRPO++ (Cameron Wolfe)
- Group Relative Policy Optimization is the dominant RL optimizer for open-source reasoning models
- Key tricks: reward shaping, curriculum learning, batch-level normalization
- Eliminates expensive reward model and value model from PPO
- Used by DeepSeek-R1, Qwen reasoning models

### ART (OpenPipe — Agent Reinforcement Trainer)
- Train multi-step agents for real-world tasks using GRPO
- Supports Qwen3.5, Llama, and other open models
- On-the-job training paradigm — agents learn from task execution
- **Directly relevant to Hermes:** could apply to tool-calling optimization

### verl (Volcano Engine)
- Hybrid RL framework for LLMs
- FSDP/FSDP2 + Megatron-LM for training
- vLLM/SGLang for rollout generation
- Accepted to EuroSys 2025

### Sebastian Raschka's Analysis
- DeepSeek-R1 used RLVR with GRPO, eliminating reward model + value model
- RL for LLM reasoning is converging on GRPO-family methods
- Key insight: simpler optimization (no value function) works better at scale

## Actionable Insights for Hermes Agent
1. **ART approach**: Hermes environments could benefit from ART-style multi-step agent training
2. **GRPO++ tricks**: Reward shaping techniques apply to Atropos environment design
3. **No value model needed**: Simplifies training pipeline significantly
4. **Curriculum learning**: Build environments with progressive difficulty


## Sources

- https://cameronrwolfe.substack.com/p/grpo-tricks
- https://github.com/OpenPipe/ART
- https://github.com/verl-project/verl
- https://magazine.sebastianraschka.com/p/the-state-of-llm-reasoning-model-training
- https://github.com/NousResearch/atropos
