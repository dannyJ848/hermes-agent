# MACLA-hierarchical-procedural-memory

*Researched: 2026-04-11 19:28 CDT*

# MACLA: Hierarchical Procedural Memory for LLM Agents

**Paper:** "Learning Hierarchical Procedural Memory for LLM Agents through Bayesian Selection and Contrastive Refinement" (AAMAS 2026)
**Authors:** Forouzandeh, Peng, Moradi, Yu, Jalili — RMIT University
**Code:** Publicly available (MACLA)

## Key Innovation
MACLA decouples reasoning from learning by maintaining a **frozen LLM** while performing all adaptation in an **external hierarchical procedural memory**. This is the 3-tier skill architecture our domain certainty engine identified as highest-priority to explore.

## Architecture (5 Components)
1. **LLM-based Procedural Abstraction** — Extracts reusable procedures from trajectories
2. **Bayesian Reliability & Utility Selection** — Tracks procedure reliability via Bayesian posteriors, selects actions via expected-utility scoring
3. **Contrastive Refinement** — Refines procedures by contrasting successes vs failures
4. **Meta-procedural Composition** — Composes lower-level procedures into higher-level meta-procedures
5. **Ontological Semantic Grounding** — Grounds procedures in semantic meaning for retrieval

## Key Results
- **78.1% avg performance** across 4 benchmarks (ALFWorld, WebShop, TravelPlanner, InterCodeSQL)
- **90.3% on ALFWorld unseen tasks** with +3.1% positive generalization
- **56 seconds** to construct memory (2,800× faster than LLM parameter-training baselines)
- **15:1 compression** — 2,851 trajectories → 187 procedures

## Relevance to Hermes Agent
- **3-tier hierarchy maps to our skill system:** atomic tool calls → procedural skills → meta-procedures
- **Bayesian selection** replaces our current confidence scoring (0-1 float) with proper posterior distributions
- **Contrastive refinement** is what our distillation pipeline is trying to do but poorly — our tip survival rates are <30% for most types
- **Frozen LLM + external memory** is exactly our architecture (Hermes doesn't fine-tune)

## Actionable Insights
1. Replace flat distilled_tips with hierarchical 3-tier structure (atomic → procedural → meta)
2. Add Bayesian reliability tracking per tip instead of simple confidence float
3. Implement contrastive refinement: compare successful vs failed trajectories to extract tips
4. 15:1 compression ratio suggests our 763 high-conf tips could be compressed to ~50 meta-procedures
5. Meta-procedural composition threshold (θ_meta) could automate skill creation from repeated tip patterns


## Sources

- https://arxiv.org/html/2512.18950v1
