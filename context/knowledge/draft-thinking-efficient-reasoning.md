# draft-thinking-efficient-reasoning

*Researched: 2026-04-19 18:57 CDT*

# Draft-Thinking: Efficient Reasoning in Long CoT LLMs (arXiv:2603.00578)

## Summary
Paper introduces "Draft-Thinking" — a 3-stage training paradigm (SFT → short RL → longer RL) that teaches LLMs to internalize concise reasoning. On Qwen3-8B, achieves 82.6% token reduction with only 2.6% accuracy drop on MATH500.

## Key Findings
1. **Reasoning depth is decidable** — models can learn WHEN to think deeply vs concisely via adaptive prompting
2. **Overthinking correlates with errors** — wrong answers are significantly longer than correct ones
3. **Progressive curriculum works** — SFT anchor → short RL → longer RL prevents reversion to verbose habits
4. **Draft mode reduces steps 111→22** — model learns to skip exploration steps and focus on computation

## Agent Implications
- Adaptive reasoning mode could let autonomous agents self-select depth per task
- Longer-than-expected outputs could serve as a real-time confusion/failure signal
- The SFT→RL progressive pattern is applicable to agent fine-tuning for tool-calling efficiency
- Chunked Symbolism format (dense symbolic representation) may improve agent planning conciseness

## Training Details
- Framework: Verl (Hybridflow) RLHF
- Hardware: 6x NVIDIA L20-48G
- Algorithm: GRPO with incremental length expansion (3000 → 6000 tokens)
- Teacher: DeepSeek-V3-0324 (685B)

## Sources

- https://arxiv.org/html/2603.00578v1
