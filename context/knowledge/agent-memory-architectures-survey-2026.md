# agent-memory-architectures-survey-2026

*Researched: 2026-04-03 07:05 CDT*

# Agent Memory Architectures: State of the Art (2026)

**Date:** April 3, 2026
**Sources:** arXiv:2512.13564 (Hu et al., 47 authors), Mem0 LOCOMO Benchmark (ECAI 2025, arXiv:2504.19413)

## Key Takeaways

### 1. New Taxonomy: Beyond Long/Short-Term Memory
The arXiv survey (2512.13564) proposes that traditional long/short-term memory taxonomies are insufficient. They introduce a **three-dimensional framework**:

**Forms (how memory is stored):**
- **Token-level memory** — explicit text in context window (ephemeral, max 1M tokens)
- **Parametric memory** — encoded in model weights via fine-tuning (permanent, expensive to update)
- **Latent memory** — compressed representations in hidden states (emerging, hard to inspect)

**Functions (what memory stores):**
- **Factual memory** — knowledge, preferences, user profiles (like Hermes MEMORY.md / Honcho)
- **Experiential memory** — past interactions, lessons learned, failure modes (like session transcripts)
- **Working memory** — current task state, scratchpad, reasoning chain (like conversation context)

**Dynamics (how memory evolves):**
- **Formation** — how new memories are created from interactions
- **Evolution** — how memories change, consolidate, or decay over time
- **Retrieval** — how relevant memories are found when needed

### 2. LOCOMO Benchmark Results (10 Approaches Compared)
The most comprehensive head-to-head comparison of memory approaches to date:

| Approach | LLM Score (Accuracy) | Median Latency | Token Cost |
|----------|----------------------|----------------|------------|
| Full-context | 72.9% | 9.87s (p95: 17.12s) | ~26,000/conv |
| Mem0g (graph-enhanced) | 68.4% | 1.09s (p95: 2.59s) | ~1,800/conv |
| Mem0 | 66.9% | 0.71s | ~1,800/conv |
| RAG | 61.0% | 0.70s | variable |
| OpenAI Memory | 52.9% | — | — |
| ReadAgent | — | — | — |
| MemoryBank | — | — | — |
| MemGPT | — | — | — |
| A-Mem | — | — | — |
| LangMem | — | — | — |

**Key insight:** Full-context is most accurate but categorically unusable in production (17s p95 latency, 14x token cost). Mem0g achieves 94% of full-context accuracy with 91% lower latency and 90% fewer tokens.

### 3. Emerging Frontiers (from the survey)
- **Memory automation** — agents autonomously deciding what to store, update, and forget
- **RL + memory** — using reinforcement learning to optimize memory operations
- **Multimodal memory** — storing images, audio, video alongside text
- **Multi-agent memory** — shared memory pools across agent teams
- **Trustworthiness** — preventing memory poisoning, ensuring privacy

### 4. Integration Landscape (Mem0 ecosystem, 2026)
21 documented integrations across:
- **Agent frameworks:** LangChain, LangGraph, LlamaIndex, CrewAI, AutoGen, Agno, CAMEL, Dify, Flowise, Google ADK, OpenAI Agents SDK, Mastra
- **Voice agents:** ElevenLabs, LiveKit, Pipecat
- **Notable pattern:** Voice agents need memory MORE urgently than text agents (users can't scroll back)

## Relevance to Hermes Agent

Hermes already implements a sophisticated memory stack:
- **Factual:** MEMORY.md (12K char), Honcho (unlimited semantic)
- **Experiential:** Session transcripts (SQLite + FTS5 search)
- **Working:** Conversation context with auto-compression

### What Hermes could adopt:
1. **Graph-enhanced memory** (like Mem0g) — Hermes's Honcho uses pgvector which is flat. Adding entity-relationship graphs could improve recall accuracy from ~67% to ~68% range.
2. **Memory automation** — Hermes's `memory_decay` + `memory_score` are basic. Could adopt survey's formation/evolution/retrieval framework.
3. **Multi-agent memory** — Hermes's subagent delegates have NO memory. Shared memory pool (via Honcho) could improve delegation quality.
4. **Latent memory** — Hermes's context compression is basic. Could explore compressed latent representations.

### What Hermes does well already:
- Multi-tier memory (MEMORY.md + Honcho + sessions) maps well to factual/experiential/working
- Memory decay and scoring exist (though could be more sophisticated)
- Semantic search via Honcho covers retrieval well

## Relevance to SOMA
SOMA's medical education context needs:
- **Factual memory:** Medical terminology, anatomy facts, bilingual EN/ES terms
- **Experiential:** User learning progress, quiz performance, weak areas
- **Working:** Current anatomy exploration state, selected structures

The LOCOMO benchmark proves that selective memory (Mem0g approach) with ~1,800 tokens delivers 68.4% accuracy vs 72.9% for full-context at 26,000 tokens. This is critical for SOMA's mobile performance constraints — we can't afford 26K tokens of context per interaction on mobile.


## Sources

- https://arxiv.org/abs/2512.13564
- https://mem0.ai/blog/state-of-ai-agent-memory-2026
- https://arxiv.org/abs/2504.19413
