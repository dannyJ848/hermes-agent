# agent-memory-episodic-salience-architecture

*Researched: 2026-04-05 04:19 CDT*

# Agent-Memory: Episodic Salience Architecture (Hightower 2026)

## Source
Rick Hightower, Spillwave Solutions (Mar 2026) — "Agent-Memory: The Key to Salient Episodic Memory for AI Agents"

## Key Architecture: Six-Layer Cognitive Stack
A Rust-powered, append-only episodic memory system that addresses AI agent amnesia.

### Core Design Principles
1. **Append-only storage** — Raw events retained indefinitely. No destructive updates.
2. **Salience detection** — Prioritizes important memories over trivial ones. Not all conversations are equal.
3. **Hierarchical summary structure** — O(log N) lookups instead of O(N) scans for episodic recall.
4. **Index eviction** — Keeps most recent and most salient memories in RAM index without unbounded growth.
5. **Library vs Episodic distinction** — Library memory = static documents/knowledge. Episodic memory = dynamic conversation history.

### Multi-Agent Memory Sharing
Supports various strategies for agents to share memory, enabling collaborative workflows.

## Relevance to Cerebrum
- **Cerebrum's 4-tier architecture** (sensory→working→episodic→semantic) maps well to this 6-layer stack
- **Salience detection** is equivalent to Cerebrum's trust scoring — both prioritize what matters
- **Append-only design** aligns with Cerebrum's episodic buffer approach
- **Index eviction** is directly applicable to our memory_decay system — evict low-salience indexed entries while keeping raw logs

## Actionable Insights for Evey
1. Implement hierarchical summaries over episodic memory for O(log N) recall instead of flat vector search
2. Add explicit salience scoring to each memory entry (not just importance + recency)
3. Consider Rust/compiled layer for high-frequency memory operations if Python becomes bottleneck
4. Multi-agent memory sharing strategies could apply to squad-dev profiles


## Sources

- https://medium.com/@richardhightower/agent-memory-the-key-to-salient-episodic-memory-for-ai-agents-70b0f8e296db
