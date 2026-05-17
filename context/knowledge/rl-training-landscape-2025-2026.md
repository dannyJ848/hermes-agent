# rl-training-landscape-2025-2026

*Researched: 2026-04-10 17:58 CDT*

# RL Training Landscape 2025→2026

## Key Paradigm Shifts
- **DeepSeek-R1** kicked off 2025 with reasoning breakthroughs via RL, shifting RL from classical agent settings to model training, optimization, reasoning, and data curation
- Three dominant RL paradigms for LLMs: RLHF (classic), RLAIF (AI feedback), RLVR (verifiable rewards) — the new promise
- **Reinforcement Pre-Training (RPT)**: RL applied during pretraining phase, not just post-training
- **Multi-objective RL**: Training with multiple reward signals simultaneously
- **Agentic RL**: RL specifically for training agent-like behaviors (tool use, planning, reasoning)

## Andrej Karpathy's Assessment
"Reinforcement Learning is terrible. It just so happens that everything else we had before was much worse."
- RL is hard but remains the best paradigm we have for real-world behavior learning

## Popular Policy Optimization Algorithms (2025)
- GRPO (Group Relative Policy Optimization) — used by DeepSeek
- PPO (Proximal Policy Optimization) — still widely used
- DPO (Direct Preference Optimization) — simpler alternative
- New variants emerging for specific domains

## Implications for Agent Training
- RLVR with verifiable rewards is most promising for agentic systems (can verify tool calls, code execution)
- Multi-objective RL could combine answer quality + format quality + execution quality (maps to ARTIST reward model)
- RPT suggests RL should start earlier in training pipeline, not just post-training fine-tuning

## Key Concerns
- RL still requires careful reward design
- Reward hacking remains a problem
- Sample efficiency is poor compared to supervised learning
- Evaluation of RL-trained models is harder than SFT models

Sources: Turing Post "AI 101: The State of RL in 2025", Sebastian Raschka "State of LLMs 2025", NVIDIA "How to Train Scientific Agents with RL"


## Sources

- https://turingpost.substack.com/p/ai-101-the-state-of-reinforcement
- https://magazine.sebastianraschka.com/p/state-of-llms-2025
- https://developer.nvidia.com/blog/how-to-train-scientific-agents-with-reinforcement-learning/
