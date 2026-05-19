# ToolBrain-RL-Agent-Tool-Use

*Researched: 2026-04-10 06:13 CDT*

# ToolBrain: Flexible RL Framework for Agentic Tool Use

**Paper:** arxiv 2510.00023 (2025)
**Authors:** ToolBrain Research, UCC, IBM Research Dublin

## Key Contributions
- Lightweight RL framework for training LLM agents to use tools
- Supports GRPO, DPO, supervised learning strategies
- Custom reward callables on execution traces OR automated LLM-as-judge rewards
- Knowledge distillation from large→small models for efficiency
- Automatic task generation from tool descriptions
- QLoRA fine-tuning via Unsloth, quantized inference via bitsandbytes

## Architecture: Brain + Agent + Adapter
- **Brain (Coach):** Selects RL strategy, manages training loop
- **Agent (Athlete):** The LLM being trained on tool use
- **Agent Adapter (Interpreter):** Translates between brain and agent formats

## Results
- Up to 30% improvement in tool-use skills on email search tasks
- CodeAct agent trained to autonomously execute multi-step tool sequences

## Relevance to Hermes/SOMA
- ToolBrain's reward callable pattern maps to Hermes' tool_call quality scoring
- Could use GRPO to train Hermes on optimal tool selection via Atropos environments
- LLM-as-judge reward matches our delegation quality scoring pattern
- Knowledge distillation pattern applicable to creating smaller, faster agent models


## Sources

- https://arxiv.org/html/2510.00023v1
- http://toolbrain.org
