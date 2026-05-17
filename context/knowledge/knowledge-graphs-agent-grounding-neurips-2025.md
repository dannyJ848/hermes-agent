# knowledge-graphs-agent-grounding-neurips-2025

*Researched: 2026-04-05 05:27 CDT*

# Knowledge Graphs as Grounding Scaffolds for Agentic AI (NeurIPS 2025)

**Source:** Sebastián Ferrada, NORA Workshop @ NeurIPS 2025 — "Memory, Meaning, and Machines: Building the Knowledge Scaffolds of Agentic AI"

## Key Insights

1. **Structured knowledge (KGs) complement LLMs** — rather than competing with neural approaches, knowledge graphs provide the scaffolding agents need for reliable at-scale operation.
2. **Three core challenges for agentic AI:** grounding, memory, and maintaining evolving world understanding.
3. **GraphRAG** as a practical pattern — combining graph-structured retrieval with LLM generation.
4. **Engineering challenges ahead:**
   - Scalable graph + vector hybrid systems
   - Evaluation of grounded agents (how to measure grounding quality?)
   - Multimodal schema design (KGs that span text, image, 3D)
   - Agent architectures that can read, write, and evolve structured knowledge

## Relevance to Cerebrum/SOMA

- Our Cerebrum memory system uses a tiered approach (sensory→working→episodic→semantic). The KG-as-scaffold pattern validates adding a structured graph layer on top of vector search.
- The "evolving structured knowledge" challenge maps directly to our epistemic trust scoring problem — memories need to be verified, decayed, and updated.
- Multimodal schema design is relevant to SOMA's bilingual medical terminology mapping (EN/ES terms → anatomical structures → 3D meshes).

## Actionable Next Steps
- Investigate GraphRAG implementations for potential integration with Honcho/Cerebrum
- Explore multimodal KG schemas for medical anatomy (linking FHIR concepts → 3D mesh regions → bilingual labels)
- Design evaluation metrics for grounded memory (precision/recall of recalled facts vs. source material)


## Sources

- https://neurips.cc/virtual/2025/136264
- https://www.linkedin.com/posts/matijafranklin_excited-to-share-our-new-paper-on-epistemic-activity-7434926766898454528-A_nB
