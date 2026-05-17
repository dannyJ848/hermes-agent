# research-extraction-sota-2026

*Researched: 2026-04-05 23:58 CDT*

# Autonomous Research Extraction: SOTA 2025-2026

## Key Systems
1. **STORM/Co-STORM** (Stanford) — Multi-agent outline-first research with source tracing. Repo: stanford-oval/storm
2. **PaperQA2** (Future-House) — RAG for scientific QA with "evidence density scoring". Repo: Future-House/paper-qa. Used to co-author a novel biology finding (2025).
3. **Elicit** — PICO-structured extraction, systematic-review-grade outputs
4. **Consensus App** — Claims-level search (not document-level), stance detection, evidence grading

## Multi-Hop Retrieval
1. **CRAG** (Corrective RAG) — Retriever → Relevance Grader → CONFIDENT/AMBIGUOUS/IRRELEVANT branching
2. **GraphRAG + DRIFT** (Microsoft) — Entity graph + Leiden communities + hybrid traversal search
3. **HopRAG** (2025) — Chunk graph with citation links, 15-25% improvement on MuSiQue
4. **LightRAG** — 10x faster than GraphRAG, dual-level retrieval
5. **RAPTOR** (Stanford) — Recursive abstractive tree for multi-level summaries

## Self-Improving Pipelines
1. **DSPy MIPROv2** — Bayesian prompt optimization over multi-step programs
2. **TextGrad** — Textual "backpropagation" through LLM chains
3. **Search-R1/ReSearch** — RL agent learns when/how to search, reward = accuracy - search_cost
4. **AgentQ** — MCTS + DPO for web browsing trajectories

## Anti-Detection Stack 2025
- **Camoufox** — Firefox anti-fingerprint (github.com/nickelc/camofox)
- **curl-impersonate** — TLS fingerprint spoofing
- **Browser-Use** — Playwright LLM agent with 2captcha integration
- **Rebrowser** — Playwright/Puppeteer leak patches

## Actionable Architecture for Evey
```
ResearchExtractionAgent:
  sources: [arXiv, PubMed, Unpaywall, SemanticScholar, PhantomExtractor]
  pipeline: discover → acquire → extract → verify → synthesize
  feedback: TextGrad-style gradient from failures → update extraction prompts
  reward: evidence_density_score - extraction_cost
```


## Sources

- stanford-oval/storm
- Future-House/paper-qa
- microsoft/graphrag
- HKUDS/LightRAG
