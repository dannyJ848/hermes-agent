# artist-tool-r1-rl-agentic-reasoning-2025

*Researched: 2026-04-07 12:52 CDT*

# ARTIST & Tool-R1: RL for Agentic Tool Use (2025)

## ARTIST: Agentic Reasoning + Tool Integration via RL (Microsoft Research, 2025)
- **Paper**: arXiv 2505.01441
- **Core idea**: Unified framework coupling agentic reasoning, RL (GRPO), and tool integration
- **Key innovation**: Adapts GRPO for agentic reasoning WITH tool use — not just text reasoning
- **Reward design**: Answer reward + Format reward + Tool Execution reward (3-component reward)
- **Results**: Beats frontier LLMs on complex math (AMC/AIME/Olympiad) and multi-turn function calling (BFCL v3, τ-bench)
- **Emergent capabilities**: Models discover agentic behaviors (self-correction, tool chaining) without explicit training
- **SOMA/Hermes relevance**: HIGH — ARTIST's 3-component reward directly applicable to Hermes agent training. Tool Execution reward addresses the exact problem of agents making wrong tool calls.

## Tool-R1: Sample-Efficient RL for Tool Use (Harbin IT / Huawei Noah's Ark, 2025)
- **Paper**: arXiv 2509.12867
- **Core idea**: RL framework for compositional multi-step tool use via Python code generation
- **Key innovation**: Dynamic sample queue to cache/reuse high-quality trajectories (reduces sampling cost)
- **Difficulty-aware data**: Categorizes tasks by difficulty, adjusts training accordingly
- **Reward**: Outcome-based (LLM answer judgment + code execution success)
- **Results**: ~10% gain over baselines on GAIA benchmark, larger gains on complex multi-step tasks
- **Code**: https://github.com/YBYBZhang/Tool-R1
- **SOMA/Hermes relevance**: HIGH — Variable sharing across steps, compositional tool invocation, reflection from environmental feedback. All directly applicable to Hermes's tool dispatch optimization.

## Group-in-Group Policy Optimization (NeurIPS 2025)
- Extends GRPO from single-turn to multi-turn agent training
- Group-in-Group structure for credit assignment across agent turns
- **Hermes relevance**: MEDIUM — Next evolution of GRPO for agent-specific RL training

## Key Takeaway for Hermes Self-Improvement
The ARTIST approach of 3-component rewards (answer + format + tool execution) is directly applicable to Hermes's distillation pipeline. Currently tips are scored by confidence — adding a "tool execution success" component would improve tip quality for tool-related skills.


## Sources

- https://arxiv.org/html/2505.01441v1
- https://arxiv.org/html/2509.12867v1
- https://neurips.cc/virtual/2025/poster/118123
