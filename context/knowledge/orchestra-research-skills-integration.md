# orchestra-research-skills-integration

*Researched: 2026-04-12 17:19 CDT*

# Orchestra Research Skills Integration (Apr 12, 2026)

## Overview
Orchestra Research provides 94 production-grade ML research skills being integrated into Hermes Agent via PR #8543. This is a "Research Skill Plane" covering the full ML lifecycle.

## Key Components

### 1. A-Evolve (Self-Evolving Agents)
- **What**: Universal infrastructure for evolving any AI agent using LLM-driven evolution algorithms
- **Pattern**: solve-observe-evolve cycles against benchmarks
- **State**: All evolvable agent state represented as files (prompts, skills, memory, tools)
- **Results**: MCP-Atlas 79.4%, SWE-bench 76.8%, Terminal-Bench 2.0 76.5%
- **Key**: Automated gating + rollback, git-versioned evolution history
- **Path**: `14-agents/a-evolve/`

### 2. Autoresearch (Two-Loop Architecture)
- **What**: Autonomous research orchestration with inner/outer loop
- **Inner Loop**: Rapid experiment iterations (hypothesis → experiment → measure → refine)
- **Outer Loop**: Synthesize results, identify patterns, steer direction
- **Key**: Fully autonomous, show progress via research presentations
- **Path**: `0-autoresearch-skill/`

### 3. GRPO Training (Production RL)
- **What**: Production-ready GRPO implementation patterns via TRL
- **Key**: Group size 4-16, no reward model needed, within-group comparisons
- **Decision Framework**: GRPO for verifiable tasks, DPO for preference pairs, PPO for subjective tasks
- **Path**: `06-post-training/grpo-rl-training/`

### 4. Additional Skills (22 categories)
- Post-training: GRPO, SimPO, Slime, TRL, VERL, OpenRLHF, MILES, TorchForge
- Agents: a-evolve, AutoGPT, CrewAI, LangChain, LlamaIndex
- Distributed Training: FSDP2, DeepSpeed
- Others: tokenization, mechanistic interpretability, data processing, safety alignment, inference serving, MLOps, RAG, prompt engineering, multimodal

## Integration Status
- Hermes PR #8543: open (feature/research-skills-integration)
- Orchestra PR #51: open (Hermes as 1st-class citizen in Orchestra NPM)
- Install: `npx` install to `~/.hermes/skills/`

## Relevance to Training Gym
- A-Evolve → Self-improvement loop with benchmarks
- GRPO → RL tool training
- Autoresearch → Autonomous research cycles
- Post-training suite → Full RL training pipeline
- Agent evolution → Directly applicable to cerebrum tip evolution


## Sources

- https://github.com/Orchestra-Research/AI-Research-SKILLs
- https://github.com/NousResearch/hermes-agent/pull/8543
- https://x.com/nousresearch/status/2043416295173968109
- https://x.com/teknium/status/2043401784413319658
