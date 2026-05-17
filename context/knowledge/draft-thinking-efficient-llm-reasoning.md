# draft-thinking-efficient-llm-reasoning

*Researched: 2026-04-13 22:25 CDT*

# Draft-Thinking: Efficient Reasoning in Long CoT LLMs

**Paper:** arXiv:2603.00578v1 (Feb 2026, Zhejiang University + Tencent)

## Key Insight
Long chain-of-thought (CoT) induces **systematic overthinking** — reasoning capability becomes coupled with reasoning cost. Most prior work uses post-hoc techniques (token compression, truncation, length penalties) without addressing core reasoning mechanisms.

## Draft-Thinking Method
1. **Draft-style reasoning structure** — Model learns a concise reasoning pattern retaining only critical steps
2. **Progressive curriculum learning** — Efficient pattern is stably internalized as capability scales
3. **Adaptive prompting** — Reasoning depth becomes a model-selectable behavior (not externally forced)

## Results
- **82.6% reduction in reasoning budget** on MATH500
- Only **2.6% performance drop** — near-lossless efficiency gain

## Relevance to Hermes Agent
- Our agent loop suffers from completion bias (overthinking token generation)
- The "draft-thinking" pattern maps to: produce concise tool calls → verify → iterate, rather than verbose reasoning chains
- Progressive curriculum learning concept applies to agent self-improvement cycles
- Adaptive prompting could inform our aggressive_continue mechanism — let the model choose reasoning depth based on task complexity

## Actionable Takeaways
1. Consider training/fine-tuning agents to produce "draft" reasoning (tool calls + minimal text) instead of verbose CoT
2. Progressive difficulty in agent training (simple tasks first → complex multi-step) mirrors curriculum learning
3. Making reasoning depth adaptive could reduce our API costs significantly

## Sources

- https://arxiv.org/html/2603.00578v1
