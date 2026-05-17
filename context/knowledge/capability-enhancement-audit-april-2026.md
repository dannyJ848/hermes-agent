# capability-enhancement-audit-april-2026

*Researched: 2026-04-13 11:58 CDT*

# Capability Enhancement Deep Audit (April 13, 2026)

## Current Infrastructure
- **Main model**: GLM-5.1 via Z.AI (ZHIPU_API_KEY)
- **Local inference**: 4 servers (Phi-3:8081, Llama-8B:8082, Nomic:8083, MiniMax:8084)
- **Web search**: SearXNG (self-hosted, free)
- **Web extraction**: Crawl4AI (built into Hermes, free)
- **Knowledge graph**: Hindsight (local, 9,945 nodes, 398K links)
- **Vector store**: Qdrant (local, free)
- **Memory**: Cerebrum SQLite (1,835 tips)
- **API keys**: ZHIPU, MOONSHOT, BRAVE, HINDSIGHT_LLM, AUXILIARY_APPROVAL, AUXILIARY_VISION
- **Missing**: OpenRouter, Firecrawl, Tavily, Exa, Jina, Gemini, OpenAI, Anthropic, SiliconFlow, Featherless

## Priority Enhancement Categories

### 1. LLM INFERENCE (biggest capability multiplier)

#### TIER 1: Free / Near-Free ($0-5/mo)
- **Google Gemini 3 Flash** — FREE tier gives 1,500 RPD (requests/day). $0.10/1M input tokens paid.
  - IMPACT: Massive. Best free model for delegation. Beats GLM-5.1 for research/summarization. Teknium recommended this.
  - COST: $0 (free tier) or ~$5/mo for moderate use
  - INTEGRATION: Simple REST API, OpenAI-compatible endpoint

- **SiliconFlow** — Has free tier models. $0.05-0.086/1M tokens for paid.
  - IMPACT: Medium. Cheapest inference for bulk eval tasks. Could replace local Phi-3 for Elo evaluation.
  - COST: $0 (free models) or ~$2-5/mo

- **OpenRouter free models** — 23 free models available via OpenRouter
  - IMPACT: Medium. Diversifies delegation pool. Already partially wired via Hermes.
  - COST: $0

#### TIER 2: Low Cost ($10-25/mo)
- **Featherless AI Basic ($10/mo)** — Flat rate, unlimited tokens, 15B models
  - IMPACT: High. Unlimited eval runs without token anxiety. Perfect for training gym.
  - COST: $10/mo flat
  - INTEGRATION: OpenAI-compatible API

- **Featherless AI Premium ($25/mo)** — Unlimited tokens, 70B+ models
  - IMPACT: Very High. Llama 4 Scout/Maverick for high-quality delegation AND unlimited eval.
  - COST: $25/mo flat
  - This is the best value for training gym — eliminates ALL token cost anxiety for evaluation.

#### TIER 3: Medium ($30-80/mo)
- **OpenRouter pay-as-you-go** — Access to 300+ models, ~$0.03/1K tokens for good models
  - IMPACT: High. One API key for Claude, GPT, Gemini, Llama, Mistral. Smart routing.
  - COST: Variable, ~$30-50/mo for moderate agent use
  - INTEGRATION: Already supported by Hermes delegate_with_model

### 2. WEB SEARCH & EXTRACTION (research speed)

#### TIER 1: Free / Near-Free ($0-5/mo)
- **Jina Reader API** — FREE for basic use, ~$0.02/1M tokens paid
  - IMPACT: Medium. Clean article extraction, sometimes better than Crawl4AI.
  - COST: $0 (free tier is generous)
  - INTEGRATION: Simple GET r.jina.ai/{url}

- **Brave Search API** — Already have API key! $5 free credit/month.
  - IMPACT: Medium-High. Better than SearXNG for some queries. Already have key, just not wired.
  - COST: $0 (already have $5 free credit/month)
  - ACTION: Wire existing BRAVE_API_KEY into research pipeline

#### TIER 2: Low Cost ($16-25/mo)
- **Firecrawl Hobby ($16/mo)** — 3,000 pages/month, 5 concurrent
  - IMPACT: Very High. The #1 web tool for agents. Scrape, extract, crawl, search. 50x faster than Apify per benchmarks.
  - COST: $16/mo
  - INTEGRATION: Native Hermes skill exists (firecrawl-fusion-browser). REST API.

- **Tavily Researcher** — 1,000 credits/mo free, $0.008/credit paid
  - IMPACT: High. Purpose-built for AI agent research. Extract + search in one call.
  - COST: $0 (free 1K/mo) or ~$8/mo for 2K extra credits

- **Exa AI** — $7/1K requests, semantic/neural search
  - IMPACT: High. Finds papers/docs by MEANING not keywords. Game-changer for research.
  - COST: ~$7-15/mo for moderate research use

### 3. AGENT TOOLING (capability expansion)

#### TIER 1: Free
- **Composio Free Tier** — Agent tool integrations (GitHub, Slack, Google, etc.)
  - IMPACT: Medium. Gives Hermes access to 250+ external tools via MCP.
  - COST: $0 (free tier)
  - INTEGRATION: MCP-compatible, has Hermes skill

- **Langfuse Self-Hosted** — Already using cloud version. Self-host = unlimited free.
  - IMPACT: Medium. Better cost tracking, no unit limits on tracing.
  - COST: $0 (self-hosted on local or VPS)

#### TIER 2: Low Cost ($10-30/mo)
- **Composio Growth ($29/mo)** — Higher rate limits, more integrations
  - IMPACT: High if we need external tool access (GitHub PRs, Slack, etc.)
  - COST: $29/mo

### 4. VECTOR / MEMORY INFRASTRUCTURE

#### TIER 1: Free
- **Qdrant Cloud Free** — Already using local Qdrant. Cloud gives redundancy.
  - COST: $0 (1 cluster, 1GB)
  - IMPACT: Low. Local Qdrant is fine.

- **MongoDB Atlas Free (M0)** — 512MB, includes Atlas Vector Search
  - COST: $0
  - IMPACT: Low-Medium. Could serve as backup knowledge store.

- **Supabase Free** — PostgreSQL with pgvector, 500MB
  - COST: $0
  - IMPACT: Low-Medium. Could replace local Qdrant if needed.

### 5. EMBEDDING MODELS

- **Jina Embeddings v3** — FREE tier, 8192 context, multilingual
  - IMPACT: High. Better embeddings than Nomic for knowledge graph and RAG.
  - COST: $0 (free tier) or very cheap
  - INTEGRATION: Simple REST API

- **Google Gemini Embedding** — FREE with Gemini API
  - IMPACT: Medium. Good quality, free.
  - COST: $0

## TOP RECOMMENDATIONS (ranked by impact/cost ratio)

### IMMEDIATE ($0 — just wiring existing keys)
1. **Wire BRAVE_API_KEY** into research pipeline (already have it, not used)
2. **Add Google Gemini 3 Flash** free API key for delegation
3. **Add Jina Reader** free tier for article extraction
4. **Self-host Langfuse** to remove cloud unit limits

### BEST VALUE ($16-25/mo)
5. **Featherless Premium ($25/mo)** — Unlimited LLM inference for training gym. This eliminates ALL token cost anxiety and lets eval flywheel run 24/7 without worrying about API costs.
6. **Firecrawl Hobby ($16/mo)** — Best web extraction for agents. Dramatically speeds up research.

### HIGH IMPACT ($30-50/mo)
7. **OpenRouter ($30-50/mo variable)** — Access to Claude, GPT, Gemini, 300+ models via one API. Smart routing.
8. **Exa AI ($7-15/mo)** — Semantic search for research. Finds papers by meaning.

### STRETCH ($80+/mo)
9. **Featherless Feather Claw Pro ($200/mo)** — All models, unlimited tokens, priority. Only if training gym becomes production-critical.
10. **Firecrawl Standard ($83/mo)** — 100K pages/month for heavy research automation.

## ESTIMATED TOTAL BY BUDGET

| Budget/mo | What You Get |
|-----------|-------------|
| $0 | Wire Brave + add Gemini Flash free + Jina Reader free + self-host Langfuse |
| $16 | Above + Firecrawl Hobby (3K pages/mo) |
| $25 | Above + Featherless Premium (unlimited LLM tokens) — BEST SWEET SPOT |
| $41 | Above + Exa semantic search |
| $50-75 | Above + OpenRouter for multi-model delegation |
| $100+ | All of the above, production-grade infrastructure |

## SPECIFIC INTEGRATION PATHS

### Gemini Flash Free (priority 1)
- Get API key from ai.google.dev
- Add to ~/.hermes/.env as GEMINI_API_KEY
- Configure as delegate model for research/summarization tasks
- Free: 15 RPM, 1M tokens/min, 1,500 RPD

### Featherless Premium (priority 2)
- Sign up at featherless.ai
- OpenAI-compatible API endpoint
- Replace local inference servers for eval — unlimited eval rounds
- Perfect for training gym 24/7 operation

### Firecrawl (priority 3)
- Sign up at firecrawl.dev
- API key in ~/.hermes/.env
- Replace SearXNG + Crawl4AI for high-quality extraction
- Already have skill: firecrawl-fusion-browser


## Sources

- https://www.firecrawl.dev/pricing
- https://featherless.ai/
- https://ai.google.dev/gemini-api/docs/pricing
- https://exa.ai/pricing
- https://www.tavily.com/pricing
- https://brave.com/search/api/
- https://jina.ai/reader/
- https://openrouter.ai/pricing
- https://www.siliconflow.com/pricing
- https://langfuse.com/pricing
- https://composio.dev/
- https://featherless.ai/blog/llm-api-pricing-comparison-2026-complete-guide-inference-costs
