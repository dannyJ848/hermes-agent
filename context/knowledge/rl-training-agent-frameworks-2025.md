# rl-training-agent-frameworks-2025

*Researched: 2026-04-10 17:19 CDT*

# RL Training for AI Agents — Frameworks & Advances (2025)

## OpenPipe ART (Agent Reinforcement Trainer)
- **URL:** https://github.com/openpipe/art (9.2k stars)
- Trains multi-step agents using GRPO for real-world tasks
- Native MCP support — "MCP•RL: Teach Your Model to Master Any MCP Server"
- Supports Qwen3.5, GPT-OSS, Llama, and more
- Serverless RL training via W&B integration
- Key insight: Multi-turn tool-calling support built in, not bolted on

## Microsoft Agent Lightning
- **URL:** https://www.microsoft.com/en-us/research/blog/agent-lightning-adding-reinforcement-learning-to-ai-agents-without-code-rewrites/
- Adds RL to agents WITHOUT code rewrites
- Separates agent execution from model training
- Converts agent experience into standardized state-action transitions
- Each transition captures LLM input, output, and reward
- Works for multi-agent workflows and dynamic tool use
- Open-source framework from Microsoft Research Asia – Shanghai

## Group-in-Group Policy Optimization (GiGPO)
- **URL:** https://arxiv.org/html/2505.10978v3
- New RL algorithm specifically for LLM agent training
- Related: OTC (Optimal Tool Calls via RL) — arXiv:2504.14870

## NVIDIA NeMo Gym + NeMo RL
- Scientific agent training with RL
- Wraps OpenAI-compatible endpoints with reasoning and tool-calling
- Evaluation and training integrated

## Key Takeaways for Hermes/SOMA
1. ART's MCP•RL approach is directly applicable — could train Hermes models on MCP tool use
2. Agent Lightning's "no rewrite" pattern means existing agent code can be RL-trained
3. GRPO remains dominant for tool-calling RL
4. State-action transition standardization is the key abstraction for multi-step agent training


## Sources

- https://github.com/openpipe/art
- https://www.microsoft.com/en-us/research/blog/agent-lightning-adding-reinforcement-learning-to-ai-agents-without-code-rewrites/
- https://arxiv.org/html/2505.10978v3
- https://developer.nvidia.com/blog/how-to-train-scientific-agents-with-reinforcement-learning/
