# agent-memory-taxonomy-survey-2026

*Researched: 2026-04-05 05:39 CDT*

# Agent Memory Taxonomy: Foundation Agents in the Second Half (Huang et al., Feb 2026)

**Source:** arXiv 2602.06052v3 — 102-author survey from UIC/UIUC/Stanford/Salesforce/Google/Meta

## Key Taxonomy (3 Dimensions)

### 1. Memory Substrates
- **External:** Vector Index, Text-record, Structural Store, Hierarchical Store
- **Internal:** Weights, Latent-State, KV Cache
- Tradeoffs: external = scalable but slow retrieval; internal = fast but limited capacity

### 2. Cognitive Mechanisms (5 types — mirrors Cerebrum!)
- **Sensory Memory** — raw input buffer (our tier 1)
- **Working Memory** — active context window (our tier 2)
- **Episodic Memory** — experiential episodes with timestamps (our tier 3)
- **Semantic Memory** — abstracted facts and knowledge (our tier 4)
- **Procedural Memory** — skills and procedures (our skills system)

### 3. Memory Operations
- Storage & Index, Loading & Retrieval, Updates & Refresh
- Compression & Summarization, Forgetting & Retention
- Multi-agent: Private-only, Shared-workspace, Hybrid, Orchestrated architectures

## Memory Learning Policies
- **Prompt-based:** Static and Dynamic (what we do now)
- **Fine-tuning:** Parameterized policies internalized into weights
- **RL for Memory:** Step-level, Trajectory-level, Cross-episode decisions

## Key Insight for Cerebrum
The paper's 5-tier cognitive mechanism taxonomy validates Cerebrum's biomimetic 4-tier design. Missing piece: **Procedural Memory** is the 5th tier we handle via skills but don't treat as a formal memory tier. Consider adding a procedural memory layer.

## Trust & Grounding (Section 9.4)
"Life-Long Personalization and Trustworthy Memory" — future direction emphasizes:
- Memory confidence scoring
- Forgetting mechanisms for stale/incorrect facts
- Multi-human-agent memory conflicts
- Continual learning without catastrophic forgetting

## Multi-Agent Memory (Section 4.2)
- **Orchestrator-based Routing:** Central controller decides memory access
- **Agent-Initiated Routing:** Agents pull from shared memory
- **Memory-driven Routing:** Memory state determines which agent handles task
- Write control for isolation, feedback loops for consistency

## Relevance to SOMA/Evey
1. Cerebrum's 4-tier model is validated by this 102-author survey
2. We should add formal Procedural Memory (skills as memory, not just tools)
3. The forgetting/retention mechanisms map directly to our memory_decay
4. RL-based memory policies could optimize our recall relevance
5. Multi-agent memory routing is relevant for squad-dev coordination


## Sources

- https://arxiv.org/html/2602.06052v3
