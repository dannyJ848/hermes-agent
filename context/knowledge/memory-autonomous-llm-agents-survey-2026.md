# memory-autonomous-llm-agents-survey-2026

*Researched: 2026-04-05 06:26 CDT*

# Memory for Autonomous LLM Agents: Comprehensive Survey (2026)

**Source:** Du (2026), arXiv:2603.07670, Hong Kong Research Institute of Technology

## Key Taxonomy: 3 Dimensions of Agent Memory

### 1. Temporal Scope
- Short-term (context window) → Working (session) → Long-term (cross-session) → Episodic (event sequences)

### 2. Representational Substrate
- Text, embeddings, structured graphs, parametric (weights), multimodal

### 3. Control Policy
- Fixed rules vs. learned policies for what to store/retrieve/forget

## 5 Mechanism Families

1. **Context-resident compression:** Summarization, sliding window, token pruning within context
2. **Retrieval-augmented stores:** Vector DBs, semantic search over persisted memories
3. **Reflective self-improving memory:** Agent reviews its own memories, identifies patterns, consolidates
4. **Hierarchical virtual context:** Multi-level memory (details → summaries → abstracts), dynamic loading
5. **Policy-learned memory management:** RL-trained policies for read/write/forget decisions

## Open Challenges (Directly Relevant to Evey)

### 9.1 Principled Consolidation
- No consensus on WHEN to consolidate (time-based vs. event-triggered vs. importance-weighted)
- Evey's Cerebrum uses biomimetic approach (sensory→working→episodic→semantic) — aligns with hierarchical pattern

### 9.2 Causally Grounded Retrieval
- Current retrieval is similarity-based (cosine on embeddings) — misses causal relevance
- Need: retrieve memories that causally explain the current situation, not just topically similar ones

### 9.3 Trustworthy Reflection
- Self-reflection can amplify biases (reflexive echo chamber)
- Need: external grounding for reflected memories (cross-source verification)

### 9.4 Learning to Forget
- Critical unsolved problem: what to prune and when
- Simple decay (time-based) is insufficient — need importance + redundancy + staleness scoring
- Evey's memory_decay tool implements basic version; needs principled upgrade

## Engineering Realities

### Staleness, Contradictions, and Drift
- Memories go stale, new information contradicts old, agents drift from reality
- Solutions: periodic re-grounding, contradiction detection, versioning

### Write Path Filtering
- Not everything should be stored — need quality gates before write
- Evey's approach: Honcho for raw storage, Cerebrum for curated semantic facts

### Three Architecture Patterns
1. **Flat store + retrieval:** Simple vector DB (Mem0, basic RAG)
2. **Hierarchical + reflective:** Multi-level with consolidation (Evey's Cerebrum)
3. **Policy-learned:** RL-trained memory manager (frontier, not yet production)

## Actionable for Evey's Cerebrum
1. **Causal retrieval:** Beyond cosine similarity — add causal chain tracing for memory recall
2. **Contradiction detection:** Before writing a new fact, check if existing facts contradict it
3. **Importance-weighted consolidation:** Not just time-decay but utility-decay (how often accessed × how important)
4. **Reflection grounding:** When Cerebrum consolidates, cross-verify against external sources
5. **Policy-learned forget:** Train a lightweight classifier on (memory → keep/forget) using past utility data


## Sources

- https://arxiv.org/html/2603.07670v1
