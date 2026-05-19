# ui-tars-2-bytedance-multi-turn-rl-gui-agents-2025

*Researched: 2026-04-05 03:11 CDT*

# UI-TARS-2: Multi-Turn RL for GUI Agents (ByteDance Seed, 2025)

**Paper:** arXiv:2509.02544
**Org:** ByteDance Seed
**Code:** https://github.com/bytedance/ui-tars, https://github.com/bytedance/UI-TARS-desktop
**Demo:** https://seed-tars.com/showcase/ui-tars-2

## Core Innovation
Native GUI agent trained with **multi-turn reinforcement learning** — unifies perception, reasoning, action, and memory through end-to-end learning with a data flywheel for scalable training.

## Architecture Components
1. **Data Flywheel** — scalable automated data generation pipeline
2. **Multi-turn RL Framework** — stabilized PPO with novel reward shaping
3. **Hybrid GUI Environment** — integrates file systems, terminals, browsers
4. **Unified Sandbox Platform** — large-scale parallel rollouts
5. **Parameter Interpolation** — merges vertical agents (GUI + Game) into one model

## Key Technical Contributions
- **In-Situ Annotation** for continual pre-training (CT)
- **Interactive Annotation** for supervised fine-tuning (SFT)
- **Decoupled GAE** and **Length-Adaptive GAE** for stable RL training
- **Value Pretraining** and **Clip Higher** modifications for PPO
- **Asynchronous Agent Rollout** via stateful environments with streaming training
- Quantization for latency reduction in production

## Benchmark Results (GUI)
| Benchmark | Score |
|-----------|-------|
| Online-Mind2Web | **88.2** |
| OSWorld | **47.5** |
| WindowsAgentArena | **50.6** |
| AndroidWorld | **73.3** |

Outperforms Claude and OpenAI agents on multiple benchmarks.

## Game Results
- Mean normalized score: **59.8** across 15-game suite (~60% human-level)
- Competitive with OpenAI o3 on LMGame-Bench

## RL Training Insights
- PPO outperforms GRPO for multi-turn agent RL
- VLM-as-Verifier viable for non-verifiable task rewards
- Value model pretraining critical for PPO stability
- Inference-time scaling (more compute = better results)
- Hybrid GUI+Game RL produces generalist agents

## Why This Matters
1. **First systematic multi-turn RL for GUI agents** — prior work mostly SFT or single-turn
2. **Data flywheel** solves data scarcity problem for agent training
3. **Cross-domain generalization** — GUI agent also works for games, info-seeking, software engineering
4. **Production-ready** — quantized models, desktop application available
5. **Hybrid environment** (GUI + terminal + filesystem) closer to real agent usage

## Relevance to SOMA/Hermes
- Multi-turn RL approach could improve Hermes browser tool reliability
- Data flywheel pattern applicable to generating training data for medical UI navigation
- Parameter interpolation technique useful for merging domain-specific agent capabilities
- Decoupled GAE + Length-Adaptive GAE are practical RL training tricks worth studying


## Sources

- https://arxiv.org/html/2509.02544v1
- https://seed-tars.com/1/
- https://github.com/bytedance/ui-tars
