# matclaw-code-first-agent-memory-apr2026

*Researched: 2026-04-08 11:34 CDT*

# MatClaw: Code-First Agent with 4-Layer Memory
**Paper**: arXiv:2604.02688 (April 2026)
**Authors**: Chenmu Zhang, Boris I. Yakobson

## Key Innovation
Code-first LLM agent for materials science that writes Python directly, no predefined tool functions. Uses 4-layer memory for multi-day coherent execution.

## Memory Architecture (4 layers)
1. **Working memory**: Current step context
2. **Episodic memory**: Recent trajectory history
3. **Semantic memory**: Learned facts and domain knowledge
4. **Procedural memory**: How-to skills and methods

## Key Results
- Per-step API accuracy ~99% with RAG over domain source code
- Handles multi-day workflows without progressive context loss
- Gap: struggles with tacit domain knowledge (timescales, equilibration protocols)
- Two interventions bridge the gap: literature self-learning + expert-specified constraints

## Applications to Evey
- 4-layer memory maps to our Cerebrum architecture (working=turn, episodic=experiences, semantic=facts, procedural=skills/tips)
- RAG over source code for tool accuracy → search tool source files before calling unfamiliar functions
- Tacit knowledge gap applies to medical domain (clinical judgment not in textbooks)
- Guided autonomy model matches Danny's workflow (he provides domain wisdom, agent handles execution)


## Sources

- https://arxiv.org/abs/2604.02688
