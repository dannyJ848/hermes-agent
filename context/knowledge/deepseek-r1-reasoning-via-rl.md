# deepseek-r1-reasoning-via-rl

*Researched: 2026-03-31 22:35 CDT*

# DeepSeek-R1: Reasoning via Pure Reinforcement Learning

## Key Insight
DeepSeek-R1-Zero is the FIRST research to validate that reasoning capabilities of LLMs can be incentivized PURELY through RL, without SFT. This is groundbreaking -- it means reasoning is an emergent property that can be trained, not just distilled.

## Architecture
- Base: DeepSeek-V3 (671B total params, 37B activated, MoE)
- DeepSeek-R1-Zero: RL directly on base model (no SFT first)
- DeepSeek-R1: Cold-start data + RL (fixes readability issues)
- Context: 128K tokens

## Training Pipeline (4 stages)
1. **SFT Stage 1**: Cold-start data (reasoning seed)
2. **RL Stage 1**: Discover reasoning patterns (self-verification, reflection, long CoT)
3. **SFT Stage 2**: Non-reasoning capabilities seed
4. **RL Stage 2**: Align with human preferences

## Emergent Behaviors from RL
- Self-verification (checking own work)
- Reflection (revising approach)
- Long chain-of-thought generation
- These emerged NATURALLY from RL, not programmed

## Distillation Finding
Distilling R1 into smaller models beats RL on those same small models. Reasoning patterns transfer better than discovering them from scratch at small scale.

## Agentic Relevance
- Self-verification and reflection are CORE agent capabilities
- The cold-start + RL pipeline could be applied to agent training
- Distillation means we can get agent-reasoning into smaller models

## Benchmarks
- MMLU: 90.8 (vs GPT-4o 87.2, o1-1217 91.8)
- GPQA-Diamond: 71.5
- SWE-bench competitive with o1
- Distill-Qwen-32B beats o1-mini

## Sources
- https://github.com/deepseek-ai/DeepSeek-R1
- Paper: DeepSeek_R1.pdf in repo


## Sources

- https://github.com/deepseek-ai/DeepSeek-R1
