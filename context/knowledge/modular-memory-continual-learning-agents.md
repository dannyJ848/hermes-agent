# modular-memory-continual-learning-agents

*Researched: 2026-04-05 05:52 CDT*

# Modular Memory for Continual Learning Agents (arXiv 2603.01761)

**Source:** Dorovatas et al. (19 authors, Dagstuhl Seminar), March 2026, arXiv:2603.01761

## Core Thesis
Combining **In-Weight Learning (IWL)** and **In-Context Learning (ICL)** through **modular memory** is the key to continual adaptation at scale. Pure parametric updates cause catastrophic forgetting; pure ICL is limited by context windows. The solution is modular memory that leverages both.

## Key Framework: Modular Memory-Centric Architecture

### ICL for Rapid Adaptation
- In-context learning allows fast knowledge accumulation without weight changes
- Suitable for episodic/experiential memory — what happened recently
- Limited by context window size — requires compression/summarization

### IWL for Stable Updates
- Weight updates provide stable, long-term capability changes
- Suitable for skill acquisition and pattern learning
- Must be low-frequency to avoid catastrophic forgetting
- "Long-term memory distilled through stable, low-frequency updates"

### Modular Design Principles
- Memory should be **modular** (not monolithic) — different modules for different memory types
- Separation of concerns: rapid adaptation vs. stable knowledge
- Memory representations should be composable and retrievable

## Relevance to Cerebrum Architecture

| Paper Concept | Cerebrum Implementation | Gap |
|--------------|------------------------|-----|
| ICL = rapid adaptation | Working memory tier (in-context injection) | ✅ Implemented |
| IWL = stable updates | Semantic memory (skill_manage, identity updates) | ⚠️ Manual, not automated |
| Modular memory | 4-tier biomimetic structure | ✅ Implemented |
| Low-frequency distillation | consolidate_daily_memory cron | ✅ Implemented |
| Compression/summarization | Episodic→semantic compression | ❌ Not yet automated |

## Key Insight for Hermes
The paper validates that **Cerebrum's tiered approach is correct** but highlights a gap: we need automated **episodic→semantic compression**. Currently, daily consolidation is manual (requires LLM calls). The "stable, low-frequency updates" pattern should be formalized:
- High-frequency: ICL via working memory (every session)
- Medium-frequency: Episodic memory (session summaries)
- Low-frequency: Semantic distillation (weekly skill consolidation)
- Very low-frequency: IWL via identity updates (monthly)

## Action Items
1. Formalize the 4-frequency update schedule in Cerebrum
2. Implement automated episodic→semantic compression (batch summarize old sessions)
3. Add "distillation frequency" metadata to Cerebrum memory entries
4. Consider when IWL (weight updates via fine-tuning) becomes necessary


## Sources

- https://arxiv.org/html/2603.01761v1
