# muse-experience-driven-self-evolving-agent

*Researched: 2026-04-12 04:19 CDT*

# MUSE: Experience-Driven Self-Evolving Agent for Long-Horizon Tasks

**Paper:** arXiv:2510.08002 (Oct 2025)
**Authors:** Cheng Yang et al. (Shanghai AI Lab)

## Key Insight
LLM agents are "test-time static" — they cannot learn from experience. MUSE introduces a **hierarchical Memory Module** that:
1. Organizes diverse levels of experience (raw trajectory → structured experience)
2. After each sub-task, autonomously reflects on trajectory
3. Converts raw trajectory into structured experience
4. Integrates back into Memory Module for future planning

## Architecture
- **Hierarchical memory**: Different abstraction levels for experience storage
- **Trajectory → Experience pipeline**: Raw execution → reflection → structured knowledge
- **Zero-shot generalization**: Accumulated experience transfers to new tasks

## Results
- SOTA on TAC (long-horizon productivity benchmark) using only Gemini-2.5 Flash
- Performance improves as agent accumulates more experience
- Strong generalization to unseen tasks

## Relevance to Hermes
Hermes's cerebrum_memory.db (episodic→semantic memory consolidation) implements a similar pattern. Key differences:
- MUSE uses hierarchical memory levels; Hermes uses tables (kg_nodes, kg_edges, distilled_tips)
- MUSE reflects per sub-task; Hermes reflects per session + cron cycles
- MUSE zero-shot generalization parallels Hermes's distilled tips cross-domain transfer

## Action Items
- Consider implementing hierarchical experience levels in cerebrum (raw → reflected → distilled → generalized)
- Per-sub-task reflection could improve tip quality over per-session reflection
- The "experience improves with accumulation" finding validates Hermes's distillation pipeline


## Sources

- https://arxiv.org/abs/2510.08002
