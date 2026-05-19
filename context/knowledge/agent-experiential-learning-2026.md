# agent-experiential-learning-2026

*Researched: 2026-04-12 02:44 CDT*

# Agent Experiential Learning (April 2026)

## ERL — Experiential Reflective Learning (ICLR 2026 MemAgents Workshop)
- **Paper:** arXiv:2603.24639 (Mar 2026)
- **Key insight:** Reflects on task trajectories → generates **heuristics** (actionable lessons) → retrieves relevant heuristics at test time → injects into agent context
- **Results:** +7.8% success over ReAct baseline on Gaia2 benchmark
- **Critical findings:**
  - Selective retrieval is essential (not dumping all heuristics)
  - Heuristics outperform few-shot trajectory prompting for transfer
  - Single-attempt experience extraction works — no need for multiple trials
- **Relevance to Hermes:** Our distilled_tips table is essentially ERL heuristics. The selective retrieval insight validates our confidence threshold (0.6). The "heuristics > trajectories" finding supports tip-based distillation over raw session replay.

## Echo — Experience Transfer for Multimodal Agents (Apr 2026)
- **Paper:** arXiv:2604.05533 (Apr 7, 2026)
- **Key insight:** Decomposes reusable knowledge into 5 dimensions: structure, attribute, process, function, interaction. Uses In-Context Analogy Learning (ICAL) for transfer.
- **Results:** 1.3x-1.7x speedup on Minecraft tasks; burst-like chain-unlocking after acquiring transferable experience
- **Critical findings:**
  - Memory as active knowledge (not passive records) dramatically improves transfer
  - Multi-dimensional knowledge decomposition enables cross-task pattern matching
  - Chain-unlocking phenomenon: once transferable experience is acquired, similar tasks get solved in rapid succession
- **Relevance to Hermes:** The 5-dimension decomposition could improve our KG node typing. Chain-unlocking mirrors what we see when tips apply across multiple tool types.

## ELITE — Experiential Learning + Intent-Aware Transfer
- **Paper:** arXiv:2603.24018 (Mar 2026)
- **Key insight:** Embodied agent framework combining experiential learning with intent-aware transfer
- **Relevance:** Intent-awareness dimension could improve our tool dispatch by understanding WHY a tool was selected, not just THAT it was selected.

## Cross-Domain Synthesis
All three papers converge on: **extract abstractions from experience, not raw trajectories**. This validates the Hermes distillation pipeline architecture (sessions → tips → confidence scoring → selective injection). The ERL finding that "heuristics > few-shot trajectories" is particularly significant — it means our distilled tips approach is theoretically sound, not just pragmatic.


## Sources

- https://arxiv.org/abs/2603.24639
- https://arxiv.org/abs/2604.05533
- https://arxiv.org/abs/2603.24018
