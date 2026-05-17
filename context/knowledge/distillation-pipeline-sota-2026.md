# distillation-pipeline-sota-2026

*Researched: 2026-04-05 01:48 CDT*

# State-of-the-Art Distillation Pipeline Design (Apr 2026)

## Key Frameworks

### 1. IBM Trajectory-Informed Memory (arXiv 2503.10600)
- **3 tip types**: Strategy (successful patterns), Recovery (failure handling), Optimization (inefficient but successful)
- **Extraction**: LLM-prompted at each decision point with window of N preceding observations
- **Format**: `IF <condition> THEN <recommendation> BECAUSE <rationale>`
- **Dedup**: Embedding similarity threshold ~0.92, then merge
- **Tiered storage**: General → Task-specific → Situational

### 2. ExpeL (arXiv 2308.10144, AAAI 2024)
- **4 insight operations**: ADD, UPVOTE, DOWNVOTE, EDIT
- Learns from BOTH successes and failures
- Successes → positive patterns
- Failures → what NOT to do + how to recover
- **Key**: Insights evolve over time — not static, living knowledge base
- Recall: similar experiences as demonstrations + extracted insights as rules

### 3. MARS (arXiv 2601.11974)
- **Single-cycle** self-improvement (no multi-turn recursion)
- **2 reflection types**:
  - Principle-based: abstract normative rules to AVOID errors
  - Procedural: step-by-step strategies for SUCCESS
- **3 phases**: Individual failure analysis → Type-topic grouping → Enhancement generation
- Outperforms Reflexion and Self-Refine at lower computational cost

### 4. Mem0 Architecture
- **Dual store**: Vector DB + Entity Graph
- **Conflict resolution**: LLM judge determines SAME/UPDATE/CONTRADICT
- **Multi-signal retrieval**: Semantic similarity + graph traversal + recency decay
- Auto-extracts atomic facts from conversations

### 5. Letta/MemGPT
- LLM manages its own memory through function calls
- **3 tiers**: Core (always in context), Archival (vector store), Recall (search)
- Proactive memory management — agent decides what to remember/forget

## Design Principles for Our Distillation Bridge

1. **Tips, not raw logs**: Extract structured tips (IF/THEN/BECAUSE), not raw tool output
2. **3-type taxonomy**: Strategy, Recovery, Optimization — from IBM paper
3. **Living insights**: ADD/UPVOTE/DOWNVOTE/EDIT — from ExpeL — not append-only
4. **Single-cycle reflection**: Principle + Procedural — from MARS — no recursion needed
5. **Conflict resolution**: LLM judge for SAME/UPDATE/CONTRADICT — from Mem0
6. **AGI roadmap awareness**: Each cycle knows its domain and past achievements

## Our Current Gap
Our bridge just writes raw JSONL entries with tool_name/status/speed. No tip extraction, no conflict resolution, no structured insights. The "lessons" column in experiences is mostly raw tool output, not actionable IF/THEN rules.

## Implementation Priority
1. **Tip Extractor**: LLM-prompted extraction of IF/THEN/BECAUSE rules from tool outcomes
2. **Tip Store**: New table with condition, recommendation, rationale, type, votes, confidence
3. **Conflict Resolver**: Before adding a new tip, check similarity to existing ones
4. **Top-Down Injection**: Inject domain-relevant tips (not raw facts) into pre_llm_call
5. **Roadmap Integration**: Each cycle logs achievements to roadmap AND to tip store


## Sources

- https://arxiv.org/html/2603.10600
- https://arxiv.org/html/2308.10144v2
- https://arxiv.org/html/2601.11974v1
- https://mem0.ai/blog/state-of-ai-agent-memory-2026
- https://github.com/letta-ai/letta
