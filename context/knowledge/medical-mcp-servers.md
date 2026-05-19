# medical-mcp-servers

*Researched: 2026-04-01 22:51 CDT*

# Medical MCP Servers — Ecosystem for SOMA

**Date:** April 2, 2026

## Overview
The medical MCP ecosystem is rapidly growing. Here are the most relevant servers for SOMA:

## Tier 1: Production-Ready

### BioMCP (★481) — genomoncology/biomcp
- **One binary, one grammar** for biomedical evidence
- Sources: PubTator3, Europe PMC, Semantic Scholar, g:Profiler, cBioPortal
- Commands: `search article`, `get gene BRAF pathways`, `study cohort`, `batch`
- MCP config: `{"command": "biomcp", "args": ["serve"]}`
- Also supports HTTP server: `biomcp serve-http`
- **SKILLS SYSTEM**: `biomcp skill install ~/.claude` — installs guided investigation workflows
- **Directly useful for SOMA**: Gene/disease/drug lookups, clinical literature search, enrichment analysis
- Install: `uv tool install biomcp-cli`

### Healthcare MCP (★104) — Cicatriiz/healthcare-mcp-public
- Node.js server with DXT extension (one-click install)
- **12 tools**: FDA Drug Info, PubMed Research, Health Topics, Clinical Trials, ICD-10 Lookup, medRxiv Search, Medical Calculator, NCBI Bookshelf, DICOM Metadata
- Caching with connection pooling
- Both stdio and HTTP/SSE interfaces
- Swagger UI for API docs
- **Directly useful for SOMA**: Drug information, ICD-10 codes, clinical trials search

## Tier 2: Specialized

### M3 (★70) — rafiattrach/m3
- Natural language queries over MIMIC-IV medical database
- Local DuckDB + Parquet or cloud BigQuery
- OAuth2 + JWT auth, SQL injection protection
- **Useful for SOMA**: Clinical data analysis patterns, demonstrating medical data access

### PubMed MCP (★8) — chrismannina/pubmed-mcp
- Advanced PubMed search with MeSH terms, date filters, author search
- Citation export (BibTeX, APA, MLA, etc.)
- Research trend analysis over time
- Article comparison
- **Useful for SOMA**: Literature search, citation management for medical content

### Medical Research MCP Suite — ezhouhou89/medical-research-mcp-suite
- Unifies ClinicalTrials.gov + PubMed + FDA
- Cross-database search and analysis

### Medical Calc MCP — u9401066/medical-calc-mcp
- 121 validated medical calculators
- Evidence-based formulas with PMID citations
- DDD architecture

### HIPAA MCP — Gautam-Galada/MCP-HIPAA
- HIPAA-compliant medical AI agent
- Role-based access control
- Local LLM inference

## Integration Strategy for SOMA

### Phase 1: Research & Education
```yaml
mcp_servers:
  biomcp:
    command: biomcp
    args: [serve]
  healthcare:
    command: npx
    args: [healthcare-mcp]
  pubmed:
    command: python
    args: [pubmed_mcp_server.py]
```

### Phase 2: Clinical Decision Support
- BioMCP for gene/drug/disease evidence
- Healthcare MCP for FDA drug data + clinical trials
- ICD-10 lookup for diagnosis coding

### Phase 3: Patient Data (Future)
- M3 pattern for querying patient records
- HIPAA MCP patterns for compliance
- FHIR API wrapping

### Key Insight
BioMCP's skill installation pattern is exactly what SOMA needs:
```bash
biomcp skill install ~/.claude --force
```
This installs guided investigation workflows as agent skills. SOMA should adopt this pattern for medical education modules.


## Sources

- https://github.com/genomoncology/biomcp
- https://github.com/Cicatriiz/healthcare-mcp-public
- https://github.com/rafiattrach/m3
- https://github.com/chrismannina/pubmed-mcp
