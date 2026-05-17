# kimi-k2.5-agent-swarm

*Researched: 2026-03-31 22:44 CDT*

# Kimi K2.5: Multimodal Agentic Model with Agent Swarm

## Key Insight
K2.5 introduces "Agent Swarm" -- transitioning from single-agent to self-directed coordinated swarm execution. It decomposes tasks into parallel sub-tasks executed by dynamically instantiated domain-specific agents. This is the same pattern we're exploring with SOMA Squad.

## Architecture
- Same MoE as K2: 1T total, 32B activated, 384 experts, 8 selected/token
- **Vision Encoder**: MoonViT (400M params)
- **Context**: 256K (up from 128K in K2)
- **Modes**: Instant (non-thinking) + Thinking modes
- **Pretraining**: 15T mixed visual+text tokens on top of K2-Base
- Native multimodality -- not bolted-on vision

## Agent Swarm
The killer feature. K2.5 can:
- Decompose complex tasks into parallel sub-tasks
- Dynamically instantiate domain-specific agents for each sub-task
- Coordinate the swarm autonomously
- Results: BrowseComp jumps from 60.6 -> 78.4 with Agent Swarm, WideSearch from 72.7 -> 79.0

## Benchmarks (competitive with GPT-5.2, Claude 4.5 Opus)
- SWE-Bench Verified: 76.8 (vs GPT-5.2: 80.0, Claude 4.5: 80.9)
- Terminal-Bench 2.0: 50.8 (vs Claude 4.5: 59.3, GPT-5.2: 54.0)
- BrowseComp w/ Agent Swarm: 78.4 (beats GPT-5.2: 65.8)
- AIME 2025: 96.1 (vs GPT-5.2: 100, Gemini 3 Pro: 95.0)
- GPQA-Diamond: 87.6

## Relevance to SOMA/Hermes
- Agent Swarm validates our multi-agent squad approach
- MoonViT vision encoder could inspire SOMA's medical imaging pipeline
- 256K context = full patient history processing
- Native multimodality means the model can process anatomy images + text together
- The "instant vs thinking" mode toggle is a great UX pattern for medical vs educational queries

## Source
- https://github.com/MoonshotAI/Kimi-K2.5 (1.6k stars)


## Sources

- https://github.com/MoonshotAI/Kimi-K2.5
