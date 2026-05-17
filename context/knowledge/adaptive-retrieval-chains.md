# adaptive-retrieval-chains

*Researched: 2026-04-11 21:16 CDT*

# Adaptive Retrieval Chains for LLM Agents

## Core Concept
Adaptive RAG dynamically decides **when and how** to retrieve based on query complexity, unlike standard RAG which blindly retrieves for every query.

## Architecture
1. **Query Analysis** — A smaller classifier model evaluates query complexity (simple vs complex, needs fresh data vs static knowledge)
2. **Strategy Selection** — Routes to: direct answer (no retrieval), internal doc search, web search, or multi-source retrieval
3. **Retrieval Phase** — Uses vector search, keyword search, or hybrid. Can iterate multiple times for complex queries, refining approach each pass
4. **Generation Phase** — LLM generates from retrieved context

## Key Insight for Agent Systems
Adaptive retrieval chains map directly to agent tool-calling loops:
- **Simple queries** → skip tools, answer from parametric knowledge (saves tokens/latency)
- **Medium queries** → single tool call (web_search or knowledge_search)
- **Complex queries** → iterative retrieval chain with refinement between passes

## Adaptive Iterative Retrieval (Han et al. 2025)
Paper in Neurocomputing (S0925231225029443): constructs search paths enabling iterative interactions between retriever and LLM in an adaptive manner. Key: the retriever and LLM form a feedback loop where each retrieval round refines the query based on previous results.

## Application to Hermes Agent
- Replace uniform `web_research` calls with complexity-classified routing
- High-value: classify query before deciding between `web_search` (fast, cheap) vs `web_extract` (slow, rich) vs `delegate_with_model` (expensive, thorough)
- The domain_certainty module already partially does this (explore_priority scoring) — could extend with query-level complexity classification

## Tools Supporting Adaptive RAG
- LangChain (query classifier + routing)
- Weaviate / Chroma (vector stores with hybrid search)
- Meilisearch (adaptive search with typo tolerance)


## Sources

- https://www.meilisearch.com/blog/adaptive-rag
- https://www.sciencedirect.com/science/article/pii/S0925231225029443
