# medical-mcp-server-free-local-2025

*Researched: 2026-04-07 13:03 CDT*

# Medical MCP Server (jamesanz/medical-mcp) - Free Local Medical Data

## Overview
A local MCP server providing free, private access to FDA, WHO, PubMed, RxNorm, and Google Scholar. No API keys needed.

## Install
```bash
npm install -g medical-mcp
# Or from source:
git clone https://github.com/JamesANZ/medical-mcp.git
cd medical-mcp && npm install && npm run build
```

## Tools Available
- **search-drugs** — Search FDA database by brand/generic name
- **get-drug-details** — Comprehensive drug info by NDC code
- **search-drug-nomenclature** — Standardized drug names via RxNorm
- **get-health-statistics** — WHO Global Health Observatory data
- **search-medical-literature** — Search 30M+ PubMed articles
- **get-article-details** — Detailed article info by PMID
- **search-google-scholar** — Academic research with citations
- **search-medical-databases** — Multi-database search

## SOMA/Hermes Relevance
- **Complement to BioMCP** — BioMCP covers genomics/clinical trials, this covers FDA drugs + WHO stats
- **No API keys** — Works out of the box, good for SOMA's offline-first design
- **Local/private** — No data leaks, important for medical apps
- **RxNorm integration** — Could enhance SOMA's medication bilingual terminology
- **PubMed search** — Backs up BioMCP's article search

## Compared to BioMCP
| Feature | BioMCP | medical-mcp |
|---------|--------|-------------|
| PubMed | ✅ | ✅ |
| Clinical Trials | ✅ | ❌ |
| FDA Drugs | ✅ | ✅ |
| RxNorm | ✅ | ✅ |
| Genomics | ✅ | ❌ |
| WHO Stats | ❌ | ✅ |
| Google Scholar | ❌ | ✅ |
| API Keys | Some needed | None needed |

Both servers are complementary — BioMCP for deep biomedical research, medical-mcp for quick drug/stat lookups.


## Sources

- https://mcpservers.org/servers/jamesanz/medical-mcp
- https://github.com/JamesANZ/medical-mcp
