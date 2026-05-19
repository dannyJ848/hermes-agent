# continually-self-improving-ai-2026

*Researched: 2026-04-04 23:23 CDT*

# Continually Self-Improving AI (Apr 2026)

## Source: arXiv 2603.18073

### Key Framework: Three Pillars
1. **Continual Knowledge Acquisition**: Synthetic continued pretraining (EntiGraph) — generates synthetic corpora from source documents, creates entity-relation graphs, enables closed-book QA that approaches RAG performance
2. **Bootstrapping Pretraining Capabilities**: Synthetic bootstrapped pretraining — nearest neighbor pairing, synthesizer-tuning, data synthesis at scale. Key insight: pretraining is the foundation of capability, not fine-tuning
3. **AI-Designed AI**: Test-time search as a path to AI designing its own architecture. AutoML + LM-based research agents

### EntiGraph Method (Relevant to Cerebrum)
- Step 1: Entity extraction from documents
- Step 2: Relation analysis between entities  
- Creates synthetic training data that preserves knowledge
- Scaling: more synthetic data → better closed-book QA
- Complements RAG (doesn't replace it)

### Karpathy Loop (Apr 2026)
- Andrej Karpathy's "autoresearch": autonomous loop where AI runs experiments indefinitely
- 700 experiments in 2 days
- Goal: engineer agents to make fastest research progress without human involvement

### Application to Evey
- Cerebrum's semantic_facts could benefit from EntiGraph-style entity-relation extraction
- Current approach: flat facts with trust scores. Better: entity-relationship graph with typed edges
- The "continual" aspect mirrors the 24/7 AGI loop already running
- Test-time search = what the iteration engine does (before_action → execute → after_action)


## Sources

- https://arxiv.org/html/2603.18073v1
- https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/
