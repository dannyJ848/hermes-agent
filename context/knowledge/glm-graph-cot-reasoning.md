# glm-graph-cot-reasoning

*Researched: 2026-04-19 22:40 CDT*

# GLM: Multi-Agent Graph Chain-of-Thought Reasoning

**Source:** arXiv:2511.01633v1

## Summary
GLM decomposes graph reasoning into 4 specialized agents (Classify → Reason → Act → Retrieve) with code-generation-based queries. Achieves 38% accuracy gain, 95.7% token cost reduction, 90.3% latency reduction vs single-agent Graph-CoT.

## Key Innovations
1. **Agent decomposition** — Classification, Reasoning, Action, Retrieval agents each handle one concern
2. **Code generation for retrieval** — Action agent generates executable Python instead of fixed function calls
3. **Priority-based KV cache eviction** — 4-tier: shared prefixes > active notebooks > completed > transient
4. **Pipelined execution** — Overlap retrieval with LLM decoding to hide latency

## Hermes Agent Relevance
- Multi-agent decomposition maps directly to Hermes tool-calling patterns
- Priority-based context eviction could optimize context window usage
- "Notebook" pattern for accumulated facts mirrors how tool results should be summarized mid-chain
- Code-generation for complex retrieval > fixed tool schemas for flexibility

## Sources

- https://arxiv.org/html/2511.01633v1
