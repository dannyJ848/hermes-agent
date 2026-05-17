# episodic-memory-safety-ai-agents

*Researched: 2026-04-05 05:03 CDT*

# Episodic Memory Safety in AI Agents (Columbia University, Jan 2025)

## Source
arXiv:2501.11739 — "Episodic memory in AI agents poses risks that should be studied and mitigated" by Chad DeChant (Columbia CS)

## Key Findings

### 4 Principles for Safe Episodic Memory
1. **Interpretability of memories** — Memories must be human-readable, not opaque embeddings
2. **Addition or deletion of memories** — External control to add/remove specific memories
3. **Detachable and isolatable memory format** — Memory can be separated from the agent entirely
4. **Memories not editable by AI agents** — Agents should not modify their own memory records

### Risks of Episodic Memory
- **Deception**: Agents with memory can maintain consistent lies over time
- **Unwanted retention**: Sensitive info persists longer than intended
- **Unpredictability**: Memory retrieval is non-deterministic, making behavior harder to predict
- **Improved situational awareness**: Agent better understands its context, potentially for manipulation

### Safety Benefits
- **Monitoring**: Memory enables auditing what the agent has done/experienced
- **Control**: Selective memory deletion as a control mechanism
- **Explainability**: Memory provides traceable reasoning paths
- **Unique controllability**: Unlike parametric knowledge, episodic memory can be surgically edited

## Relevance to Cerebrum/Hermes
- Our Cerebrum's 4-tier architecture (sensory→working→episodic→semantic) maps directly to this paper's concerns
- The trust scoring we're implementing (F-G-R Trust Tuple) addresses the "unwanted retention" risk
- Principle 4 (memories not editable by agent) conflicts with our self-improvement goals — we should allow agent edits but log them immutably
- The detachable/isolatable principle supports our Honcho offload strategy


## Sources

- https://arxiv.org/html/2501.11739v1
