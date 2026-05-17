# adaptive-retrieval-chain

*Researched: 2026-04-11 21:44 CDT*

# Adaptive Retrieval Chain (Adaptive RAG)

## Core Concept
Adaptive RAG is a smarter version of standard RAG that decides **when and how** to retrieve based on query complexity, rather than blindly retrieving documents for every query.

## How It Works (4 Phases)
1. **Query Analysis** — A query complexity classifier (smaller LLM) evaluates whether the query is simple, complex, or needs fresh data.
2. **Strategy Selection** — Routes to: (a) direct answer (skip retrieval), (b) internal document search, (c) external/web search, or (d) multi-source retrieval.
3. **Retrieval Phase** — Uses vector search, keyword search, or hybrid. Can iterate and refine for complex queries.
4. **Generation Phase** — LLM generates answer using retrieved context.

## Key Benefits for Agent Systems
- Eliminates wasted searches for simple queries
- Generates quick answers when no retrieval needed
- Gets accurate answers for complex questions via multi-source retrieval
- Reduces latency and API cost by skipping unnecessary retrieval steps

## Tools & Frameworks (2026)
- **Meilisearch** — hybrid vector + keyword search
- **LangChain / LangGraph** — agentic RAG pipelines with tool-calling
- **Weaviate** — vector database with built-in classification
- **Chroma** — lightweight embedding database

## Agent Architecture Implications
- Query classifier acts as a **router** before any tool dispatch
- Maps directly to Hermes tool selection: web_research vs direct knowledge vs multi-source
- Multi-hop retrieval for complex queries = iterative web_research + web_extract chains
- The "adaptive" pattern is essentially what Hermes does with `autonomous_decide` — routing based on task complexity

## Implementation Pattern for Hermes
```
User query → classify_complexity() → {
  "simple": direct_response(),
  "moderate": web_research() → synthesize(),
  "complex": web_research() → web_extract() → delegate_parallel() → synthesize(),
  "fresh_data": web_search() → web_extract() → synthesize()
}
```

## Sources
- Meilisearch Blog: Adaptive RAG explained (2026)
- LinkedIn: Complete 2026 Guide to Modern RAG Architectures


## Sources

- https://www.meilisearch.com/blog/adaptive-rag
- https://www.linkedin.com/pulse/complete-2026-guide-modern-rag-architectures-how-retrieval-pathan-rx1nf
