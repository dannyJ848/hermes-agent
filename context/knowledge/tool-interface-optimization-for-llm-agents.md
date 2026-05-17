# tool-interface-optimization-for-llm-agents

*Researched: 2026-04-06 05:43 CDT*

# Tool Interface Optimization for LLM Agent Reliability

**Paper:** "Learning to Rewrite Tool Descriptions for Reliable LLM-Agent Tool Use" (arXiv:2602.20426)
**Authors:** Ruocheng Guo, Kaiwen Dong, Xiang Gao, Kamalika Das

## Key Insight
Agent performance depends not just on the agent's reasoning but on **tool interface quality**. Human-written tool descriptions become a bottleneck when agents must select from 100+ candidate tools. Optimizing tool descriptions is a practical complement to agent fine-tuning.

## Trace-Free+ Framework
- **Curriculum learning** that progressively transfers supervision from trace-rich to trace-free settings
- Encourages the model to abstract reusable interface-usage patterns
- Works in **cold-start scenarios** where execution traces are unavailable
- Generalizes to unseen tools across domains

## Results
- Consistent gains on StableToolBench and RestBench
- Strong cross-domain generalization
- Robust when candidate tools scale to 100+
- Tool interfaces optimized independently can still generalize

## Relevance to Hermes Agent
Our tool calling has ~34% failure rate on web_extract. Rather than only improving the agent, we could **rewrite tool descriptions** to be more machine-readable. This paper's framework could be applied to:
1. Rewrite Hermes plugin tool descriptions for better model selection
2. Generate optimized parameter schemas from usage traces
3. Curriculum approach: start from tools we have traces for, generalize to new ones

## Methodology Pipeline
1. Agentic seed tool annotation + filtering
2. User query synthesis
3. Trace collection (when available)
4. Tool description generation (trace-driven or trace-free)
5. Evaluation via teacher-forcing on unseen tools


## Sources

- https://arxiv.org/html/2602.20426
