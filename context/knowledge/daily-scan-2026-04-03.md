# daily-scan-2026-04-03

*Researched: 2026-04-03 07:02 CDT*

# Daily Intelligence Scan — April 3, 2026

## Agent Memory State of the Art (Mem0 LOCOMO Benchmark)

**Source:** Mem0 blog (April 1, 2026) + ECAI 2025 paper (arXiv:2504.19413)

Key benchmark results from the broadest memory comparison to date (10 approaches, LOCOMO dataset):

| Approach | Accuracy | Latency (median) | Token Cost |
|----------|----------|-------------------|------------|
| Full-context | 72.9% | 9.87s (p95: 17.12s) | ~26K/convo |
| Mem0g (graph) | 68.4% | 1.09s (p95: 1.44s) | ~1,800/convo |
| Mem0 (basic) | 66.9% | 0.71s | ~1,800/convo |
| RAG | 61.0% | 0.70s | - |
| OpenAI Memory | 52.9% | - | - |

**Implications for Hermes/Honcho:**
- Selective memory pipelines (like Honcho) are the right architecture — 91% lower latency, 90% fewer tokens for ~6pt accuracy tradeoff
- Graph-enhanced memory outperforms flat vector retrieval by 1.5pts — validates Honcho's dialectic/peer card approach
- OpenAI's built-in memory scores only 52.9% — bespoke systems significantly outperform generic solutions

## Notable New Repos (GitHub, last 24h)

### 1. open-brain-server (Bobby-cell-commits)
- MCP memory server, 14 tools, hybrid BM25+pgvector search
- Knowledge graph, auto-dedup, salience ranking
- Supabase + pgvector, Edge Functions (Deno/TS)
- Ingestion pipelines for Reddit, RSS, HuggingFace Papers
- **Relevance:** Architecture similar to Honcho but with ingestion pipelines — could inspire automated knowledge ingestion for Hermes

### 2. agent-men / Memory OS (zhaoyaoyuan)
- Persistent memory for AI agents, TypeScript
- 5 structured memory types: fact, constraint, preference, task_state, experience
- Event ingestion → LLM extraction → similarity recall → SQLite storage
- Evidence traceability (every memory linked to source event)
- **Relevance:** The 5-type taxonomy is cleaner than our current approach. "experience" type for lessons learned is exactly what learn_from_interaction does. Worth considering a type taxonomy for Honcho memories.

### 3. SkillsVote (MemTensor)
- Agent-native skill recommendation engine
- Just-in-time dynamic routing to skills
- Token efficiency optimization via smart skill selection
- **Relevance:** Could inspire a skill recommendation layer for Hermes — instead of loading all skills, dynamically route to relevant ones

### 4. RustyHand (ginkida)
- Agent OS in Rust, 134K LOC, 10 crates
- 37 agents, 26 LLM providers, 37 messaging channels
- MCP server + A2A protocol, 120+ API endpoints
- **Relevance:** A2A (Agent-to-Agent) protocol support is emerging as a standard — worth tracking

### 5. ccxray (lis186)
- X-ray vision for AI agent sessions
- Transparent HTTP proxy + dashboard for Claude Code
- **Relevance:** Session introspection tooling — useful for Dojo analysis

## Research Papers

### "Why Reasoning Fails to Plan" (arXiv:2601.22311)
- LLMs reason well step-by-step over short horizons but fail at long-horizon planning
- Planning-centric analysis shows disconnect between reasoning and planning
- **Relevance:** Validates Hermes's iterative execution approach (verify-after-write, checkpoint before risky ops) — avoid relying on LLM planning for complex multi-step tasks

### MagicAgent (arXiv:2602.19000)
- Foundation models for generalized agent planning
- Planning-specific training improves agent performance

## Cross-Reference: Actionable for Hermes/SOMA

1. **Memory type taxonomy** — Adopt a structured type system for Honcho memories (fact, constraint, preference, task_state, experience)
2. **Graph-enhanced retrieval** — Already in Honcho via dialectic peer cards, but the 1.5pt boost validates the approach
3. **Ingestion pipelines** — Open-brain-server's auto-ingestion from RSS/Papers could automate our daily scan
4. **A2A protocol** — Emerging standard for multi-agent communication, track for future


## Sources

- https://mem0.ai/blog/state-of-ai-agent-memory-2026
- https://github.com/Bobby-cell-commits/open-brain-server
- https://github.com/zhaoyaoyuan/agent-men
- https://github.com/MemTensor/skills-vote
- https://github.com/ginkida/rustyhand
- https://github.com/lis186/ccxray
- https://arxiv.org/abs/2601.22311
