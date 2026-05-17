# elephantbroker-knowledge-grounded-cognitive-runtime

*Researched: 2026-04-05 04:36 CDT*

# ElephantBroker: Knowledge-Grounded Cognitive Runtime for Trustworthy AI Agents

**Source:** arxiv:2603.25097v1 (March 2026) by Cristian Lupascu, Alexandru Lupascu
**URL:** https://arxiv.org/html/2603.25097v1

## Key Innovation
ElephantBroker is an open-source cognitive runtime that unifies Neo4j knowledge graph + Qdrant vector store via Cognee SDK to provide durable, verifiable agent memory.

## Architecture Highlights

### 1. Hybrid Five-Source Retrieval Pipeline
Retrieves from 5 different sources (not just vector similarity) for richer context assembly.

### 2. Eleven-Dimension Competitive Scoring Engine
Budget-constrained context assembly scoring memories across 11 dimensions:
- Two-pass scoring: independent dimensions first, then interaction-dependent dimensions
- Budget-constrained selection ensures context window is optimally filled

### 3. Four-State Evidence Verification Model
Tracks provenance and trustworthiness of stored knowledge through 4 evidence states.

### 4. Nine-Stage Consolidation Engine
Strengthens useful patterns while decaying noise — directly applicable to Cerebrum's consolidation needs.

### 5. Five-Stage Context Lifecycle
Goal-aware assembly with continuous compaction.

### 6. Six-Layer Guard Pipeline + AI Firewall
Cheap-first safety enforcement with enforceable tool-call interception.

### 7. Numeric Authority Model
Multi-organization identity with hierarchical access control.

## Relevance to Cerebrum/Hermes

The **11-dimension scoring engine** maps well to our epistemic trust scoring (F-G-R Trust Tuple). Their dimensions likely include:
- Source provenance (who said it)
- Verification status (tool-confirmed vs. hallucinated)
- Temporal relevance (recency)
- Access frequency (usage patterns)
- Goal alignment (current task relevance)

The **4-state evidence verification** model provides a framework for Cerebrum's trust scoring:
- Could map to: UNVERIFIED → PARTIALLY_VERIFIED → VERIFIED → DEPRECATED
- Each state transitions based on grounding evidence (tool calls, cross-source confirmation)

The **9-stage consolidation engine** is structurally similar to Cerebrum's memory tiers (sensory→working→episodic→semantic) and could improve our decay/consolidation logic.

## Actionable Next Steps
1. Study the 11 scoring dimensions in detail — adapt for Cerebrum's trust scoring
2. Implement 4-state evidence verification in our memory pipeline
3. Consider Neo4j for relational memory (currently using SQLite+Qdrant)
4. Evaluate Cognee SDK as a potential memory layer


## Sources

- https://arxiv.org/html/2603.25097v1
