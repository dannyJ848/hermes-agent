# biomcp-integration-soma-medical-research

*Researched: 2026-04-02 20:09 CDT*

# BioMCP Integration for SOMA Medical Research (April 2026)

## Setup
- BioMCP v0.8.19 installed in hermes-agent venv
- Configured as MCP server in ~/.hermes/config.yaml
- Sources: PubMed, ClinicalTrials.gov, FDA, Semantic Scholar, Europe PMC, PharmGKB, g:Profiler, UniProt, ClinVar, gnomAD, OncoKB

## Verified Capabilities
- **Article search**: `search article -k "query"` — returns PMID, title, date, citations
- **Article details**: `get article <PMID>` — full abstract, DOI, journal, authors, open access status
- **Gene lookup**: `get gene BRAF`
- **Drug info**: `search drug --region us`
- **Disease trials**: `search trial -c melanoma`
- **Cross-entity**: `search all --gene BRAF --disease melanoma`

## Key Papers Found for SOMA
1. **PMID 40633961** (BMJ Qual Saf, 2025): GPT-4 achieves 97% accuracy in EN→ES medical translation. Only ≤1% potential for harm at sentence level. Validates SOMA's LLM-based bilingual approach.
2. **PMID 41747275** (JMIR Form Res, 2026): Focus groups show patients AND physicians want 3D/AR visualizations for patient education. Patients prefer interactive 3D over 2D diagrams.
3. **PMID 41915705** (2026): Real-time medical simulation systems — relevant for SOMA's physiology simulation.

## SOMA Use Cases
1. **Education content enrichment**: Auto-search for latest papers on each body region
2. **Drug interaction data**: Pull FDA adverse events and clinical trial data
3. **Terminology validation**: Cross-reference medical terms across PubMed/Semantic Scholar
4. **Bilingual accuracy**: Verify EN/ES terminology against published literature

## Performance Notes
- Semantic Scholar rate-limited without S2_API_KEY (1 req/2sec)
- PubMed works well with NCBI_API_KEY for higher throughput
- Europe PMC is the fastest source

## Sources

- https://github.com/biomcp/biomcp
- https://pubmed.ncbi.nlm.nih.gov/
