# agent-memory-architecture-patterns-2025

*Researched: 2026-04-05 04:33 CDT*

# Agent Memory Architecture Patterns (2025-2026 Research)

## Key Papers
- **Agent Memory Survey** (47 authors, Dec 2025): Unified taxonomy — memory forms (storage), functions (purpose), dynamics (change). Three dimensions must be separated.
- **A-MEM**: Zettelkasten-style knowledge network with retroactive bidirectional links. Memory as graph, not list.
- **SYNAPSE**: Spreading activation with dual-layer architecture. F1=40.5 on LoCoMo benchmark (+7.2 over next best), 95% token reduction vs full-context.
- **Mem0**: Graph-augmented memory via FalkorDB, per-user graph isolation, <140ms p99 latency, 26% relative improvement.
- **Procedural Memory Is Not All You Need**: LLMs mirror human procedural memory but lack grounded factual/semantic knowledge. Need separate modules.

## Core Insights for Cerebrum/Hermes Architecture

1. **Graph > Flat Vectors**: For multi-session reasoning, graph traversal (relatedness) beats similarity search (look-alike). Cerebrum's tiered approach should add bidirectional linking between episodic entries.

2. **Multiple Memory Systems**: A fact store ≠ episode log ≠ skill library. Build separate modules with clean interfaces (microservice composition). MAP paper demonstrates modular planner architecture.

3. **Salience Scoring at Write Time**: Agent-memory uses TOC nodes with immutable storage + importance classification at encoding. Aligns with Cerebrum's sensory→working→episodic→semantic tiering.

4. **Spreading Activation**: SYNAPSE's dual-layer with weighted activation spreading dramatically reduces token consumption while improving retrieval quality. Relevant to Honcho's semantic search.

5. **Trust/Grounding Gap**: No paper explicitly addresses epistemic trust scoring (how to verify if a stored memory is grounded vs speculative). This is a gap — Cerebrum's F-G-R Trust Tuple approach is novel.

## Action Items for SOMA/Cerebrum
- Add bidirectional links between episodic memories (A-MEM pattern)
- Consider FalkorDB-style graph augmentation for Honcho queries
- Implement salience scoring at write time (classify importance during encoding)
- Epistemic trust scoring remains an unexplored research frontier

## Sources

- https://dev.to/tfatykhov/your-ai-agent-has-amnesia-and-you-designed-it-that-way-pf8
- https://medium.com/@richardhightower/agent-memory-the-key-to-salient-episodic-memory-for-ai-agents-70b0f8e296db
- https://atlan.com/know/memory-layer-for-ai-agents/
