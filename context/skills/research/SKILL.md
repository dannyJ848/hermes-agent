---
name: research
version: 2.0
description: Research skills — umbrella covering academic paper discovery, web search, systematic deep research, knowledge base building, prediction markets, domain intelligence, and daily intelligence scanning.
trigger: When researching topics, searching for papers, building knowledge bases, monitoring trends, or gathering intelligence.
---

# Research Skills

## Academic Paper Discovery

### arXiv Search

Search and retrieve academic papers from arXiv via free REST API. No API key needed.

| Action | Command |
|--------|---------|
| Search papers | `curl "https://export.arxiv.org/api/query?search_query=all:QUERY&max_results=5"` |
| Get specific paper | `curl "https://export.arxiv.org/api/query?id_list=2402.03300"` |
| Read abstract (web) | `web_extract(urls=["https://arxiv.org/abs/2402.03300"])` |
| Read full paper (PDF) | `web_extract(urls=["https://arxiv.org/pdf/2402.03300"])` |

**Search syntax**: `all:KEYWORD`, `ti:TITLE`, `au:AUTHOR`, `cat:cs.AI`, `submittedDate:[20240101 TO 20241231]`

**Rate limits**: 1 req/3s per IP. Use `sleep 3` between calls. For bulk: mirror at `https://r.jina.ai/http://export.arxiv.org/api/query?...`

### arXiv Direct API Fallback

When `web_search` returns "Payment Required" or `web_research` returns "Neither Firecrawl nor SearXNG configured":

```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
import requests
url = 'http://export.arxiv.org/api/query?search_query=all:KEYWORD1+AND+all:KEYWORD2&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending'
r = requests.get(url, timeout=15)
print(r.text[:4000])
"
```

### ML Paper Writing

Write publication-ready ML/AI papers for NeurIPS, ICML, ICLR, ACL, AAAI, COLM:
- LaTeX templates, citation verification, reviewer guidelines
- Conference checklists, statistical analysis with SciencePlots
- Dependencies: semanticscholar, arxiv, habanero, requests, scipy, numpy, matplotlib

### Research Paper Writing Pipeline

End-to-end pipeline: experiment design → literature review → execution → analysis → writing → review → revision → submission.
- Iterative loop: results trigger new experiments, reviews trigger new analysis
- Phase 0: Project Setup → Phase 1: Literature Review → Phase 2: Experiments → Phase 3: Analysis → Phase 4: Writing → Phase 5: Review → Phase 6: Revision → Phase 7: Submission

## Web Search & Extraction

### DuckDuckGo Search

Free web search via DuckDuckGo. No API key required.

```bash
pip install ddgs

# Python API
from duckduckgo_search import DDGS
with DDGS() as ddgs:
    results = ddgs.text("query", max_results=5)
    for r in results:
        print(r['title'], r['href'], r['body'])
```

### Browser Research Fallback

When `web_search`, `web_research`, and `web_extract` all fail:

```python
# arxiv.org search via browser
browser_navigate(url="https://arxiv.org/search/?searchtype=all&query=YOUR+TERMS&start=0")
browser_console(expression="Array.from(document.querySelectorAll('.title')).slice(0,15).map(e => e.textContent.trim()).join('\n')")
```

### Parallel CLI (Optional Vendor Skill)

Agent-native web search, extraction, deep research, enrichment, FindAll, monitoring.
- JSON output via `--json`, non-interactive, async jobs with `--no-wait`
- Paid service with free tier. Prefer Hermes native `web_search` / `web_extract` by default.
- Use when user mentions Parallel specifically or needs enrichment/FindAll/monitor workflows.

## Systematic Deep Research

Multi-phase methodology inspired by DeerFlow:

**Phase 1: Broad Exploration** — Map the territory. Initial survey, identify dimensions, stakeholders, unknowns.
**Phase 2: Deep Dive per Dimension** — 3-5 searches per dimension. Verify sources, extract specifics, find contradictions.
**Phase 3: Synthesis** — Cross-reference findings. Resolve contradictions. Build narrative.
**Phase 4: File into Knowledge Base** — Save to `~/.hermes/knowledge/` with proper citations.

Core principle: "A single search query is NEVER enough."

## Knowledge Base Building

### LLM Wiki (Karpathy Pattern)

Build persistent, compounding knowledge base as interlinked markdown files.
- Unlike RAG (rediscovers per query), wiki compiles once and keeps current
- Cross-references already there, contradictions already flagged
- Division of labor: human curates sources, agent summarizes and maintains
- Location: `~/.hermes/knowledge/` or custom wiki directory

### GitNexus Explorer

Index codebase into knowledge graph, serve interactive web UI:
- Zero-server, browser-based code intelligence
- Prerequisites: Node.js v18+, git, GitNexus at `~/.local/share/gitnexus`
- Build: `cd ~/.local/share/gitnexus && npm install && npm run build`
- Index: `node dist/index.js /path/to/repo`
- Serve: `node dist/server.js --port 3456`

## Daily Intelligence Scan

Automated daily scan for AI agent repos, LLM papers, breakthroughs (runs as cron at 7AM):

**Step 1: GitHub Trending**
```bash
gh search repos --sort stars --limit 15 --created ">$YESTERDAY" "AI agent"
gh search repos --sort stars --limit 15 --created ">$YESTERDAY" "multi-agent"
gh search repos --sort stars --limit 10 --created ">$YESTERDAY" "MCP model context protocol"
```

**Step 2: README Content** — Use `raw.githubusercontent.com` URLs, NOT `github.com` (returns navigation HTML)

**Step 3: arXiv Papers** — Search for "agent" OR "multi-agent" OR "MCP" in cs.AI, cs.CL, cs.LG

**Step 4: Web News** — Search for "AI agent breakthrough" OR "LLM reasoning" with date filter

## Domain Intelligence (Passive OSINT)

Passive domain reconnaissance using Python stdlib. Zero dependencies, zero API keys.

```bash
python3 SKILL_DIR/scripts/domain_intel.py subdomains example.com    # CT log discovery
python3 SKILL_DIR/scripts/domain_intel.py ssl example.com           # Certificate inspection
python3 SKILL_DIR/scripts/domain_intel.py whois example.com         # Registrar lookup
python3 SKILL_DIR/scripts/domain_intel.py dns example.com           # DNS records
python3 SKILL_DIR/scripts/domain_intel.py available coolstartup.io  # Availability check
```

## Prediction Markets

### Polymarket

Query prediction market data via public REST APIs. No authentication required.

- **Events** contain **Markets** (1:many)
- **Markets** are binary outcomes with Yes/No prices (0.00-1.00)
- Prices ARE probabilities: 0.65 = 65% likely
- `outcomePrices`: JSON array `["0.80", "0.20"]`
- `clobTokenIds`: JSON array of token IDs [Yes, No]

Endpoints: events, markets, prices, orderbooks, history. See `references/api-endpoints.md` for full reference.

## Hermes Repo Tracker

Daily check of `NousResearch/hermes-agent` for new commits, releases, PRs, changelog updates.
- GitHub API (no auth needed): `https://api.github.com/repos/NousResearch/hermes-agent`
- Commits, releases, issues, PRs, file changes — all via API
- Auto-update agent when new releases drop

## Pitfalls

- **arXiv rate limits**: 1 req/3s. Use mirrors or add delays.
- **GitHub README extraction**: Use `raw.githubusercontent.com`, not `github.com` URLs.
- **web_search failures**: Have 3 fallbacks ready: web_research → web_extract → browser fallback → arXiv direct API.
- **SearXNG dependency**: If not deployed, DuckDuckGo or browser fallback works.
- **Research depth**: One search is never enough. Minimum 3 angles per topic.
- **Citation verification**: Always verify citations with Semantic Scholar or arXiv before including in papers.
- **Parallel CLI**: Paid service — don't prefer by default over native tools.
