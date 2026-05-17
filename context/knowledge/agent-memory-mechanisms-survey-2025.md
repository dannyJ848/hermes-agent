# agent-memory-mechanisms-survey-2025

*Researched: 2026-04-05 08:03 CDT*

# Agent Memory Mechanisms Survey (Feb 2026, arXiv 2602.06052)

**Paper:** "Rethinking Memory Mechanisms of Foundation Agents in the Second Half: A Survey"
**Authors:** Wei-Chieh Huang, Weizhi Zhang et al. (UIC, UIUC, Stanford, Salesforce, Google, Meta, etc.)

## Key Taxonomy — 3 Dimensions of Agent Memory

### 1. Memory Substrates
- **External:** Vector Index, Text-record, Structural Store, Hierarchical Store
- **Internal:** Weights, Latent-State, KV Cache
- Tradeoffs between external (scalable, slower) vs internal (fast, limited)

### 2. Cognitive Mechanisms (5 types)
- **Sensory Memory** — raw input buffering
- **Working Memory** — active context window
- **Episodic Memory** — experience replay, past interactions
- **Semantic Memory** — generalized facts/knowledge
- **Procedural Memory** — learned skills/policies

### 3. Memory Subjects
- **User-Centric** — personalized per user
- **Agent-Centric** — agent's own knowledge

## Memory Operations
- Storage/Index, Loading/Retrieval, Updates/Refresh
- Compression/Summarization, Forgetting/Retention
- Multi-agent: Private-only, Shared-workspace, Hybrid, Orchestrated architectures

## Learning Policies
- Static prompt-based control
- Dynamic prompt-based control
- Fine-tuning for parameterized memory policies
- RL for step-level, trajectory-level, and cross-episode memory decisions

## Evaluation Metrics
- Accuracy-based, Similarity-based, LLM-as-judge

## Future Directions
1. Memory for continual learning and self-evolving agents
2. Multi-human-agent memory organization
3. Memory infrastructure and efficiency
4. Life-long personalization and **trustworthy memory**
5. Multimodal, embodied, world-model agents

## Relevance to Evey/Cerebrum
- Our 4-tier biomimetic memory (sensory→working→episodic→semantic) maps directly to their cognitive taxonomy
- **Trustworthy Memory** (Section 9.4) validates our epistemic trust scoring approach
- Forgetting/Retention mechanisms align with our memory_decay tool
- Their "compression and summarization" matches our consolidation pipeline
- Multi-agent memory isolation is relevant for squad-dev profiles

## Key Insight
The paper confirms that the field is converging on biomimetic memory architectures. The "second half" of AI is about memory management in real-world, long-horizon environments — exactly what Cerebrum is designed for. Trust scoring and epistemic grounding remain under-explored in the literature, giving our approach novelty.


## Sources

- https://arxiv.org/html/2602.06052v3
