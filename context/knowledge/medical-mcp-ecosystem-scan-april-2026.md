# medical-mcp-ecosystem-scan-april-2026

*Researched: 2026-04-03 07:08 CDT*

# Medical MCP Server Ecosystem Scan (April 2026)

**Date:** April 3, 2026
**Sources:** github.com/sunanhe/awesome-medical-mcp-servers, github.com/Cicatriiz/healthcare-mcp-public

## Overview
The medical MCP ecosystem is rapidly expanding. The awesome-medical-mcp-servers repo (64 stars) catalogs 12+ servers, and healthcare-mcp-public (104 stars) is emerging as the most comprehensive single-server solution.

## Tier 1: Directly Relevant to SOMA

### 1. mcp-slicer (zhaoyouj/mcp-slicer)
- **What:** Connects 3D Slicer with MCP clients (Claude Desktop, Cline)
- **SOMA Relevance:** ★★★★★ — Natural language control of medical image processing, scene creation, and manipulation
- **Potential:** Could replace SOMA's custom mesh pipeline with 3D Slicer's battle-tested processing via MCP
- **Status:** Experimental but functional

### 2. healthcare-mcp-public (Cicatriiz/healthcare-mcp-public) — 104★, 28 forks
- **What:** Comprehensive Node.js MCP server with FDA drugs, PubMed, medRxiv, NCBI Bookshelf, clinical trials, ICD-10, DICOM metadata, medical calculator
- **SOMA Relevance:** ★★★★☆ — All-in-one medical knowledge backend
- **Features:** DXT package for one-click install, Docker support, Railway deployment
- **Potential:** Could serve as SOMA's medical knowledge API layer, replacing custom endpoints

### 3. medadapt-content-server (ryoureddy/medadapt-content-server)
- **What:** MCP server for AI-assisted medical learning — fetches educational resources from PubMed, NCBI Bookshelf, user docs
- **SOMA Relevance:** ★★★★☆ — Directly aligns with SOMA's medical education mission
- **Potential:** Content pipeline for SOMA's encyclopedia and bilingual medical terms

### 4. agentcare-mcp (Kartha-AI/agentcare-mcp)
- **What:** FHIR + EMR integration (Cerner, Epic) via MCP
- **SOMA Relevance:** ★★★☆☆ — Clinical workflow integration, useful if SOMA expands to clinical settings
- **Note:** Uses Claude Desktop and Goose Desktop as clients

## Tier 2: Supporting Infrastructure

### 5. dicom-mcp (ChristianHinge/dicom-mcp)
- DICOM server interactions (PACS/VNA) — already in Hermes skills
- SOMA could use for loading DICOM datasets in development

### 6. bio-mcp (acashmoney/bio-mcp)
- Protein structure analysis via MCP
- Relevant if SOMA adds molecular/cellular level content

### 7. mcp-simple-pubmed (andybrandt/mcp-simple-pubmed)
- PubMed article access via Entrez API
- Lightweight alternative to BioMCP for literature search

### 8. medical-mcp (chris-lovejoy/medical-mcp)
- NICE (UK) clinical guidelines via MCP
- Useful for SOMA's "Professional" tier explanations

### 9. Medical_calculator_MCP (johnyquest7/Medical_calculator_MCP)
- Medical calculations via MCP
- Relevant for SOMA's clinical calculators feature

## Key Insight for SOMA Architecture
The MCP ecosystem is converging on a pattern where each domain (imaging, literature, terminology, clinical) gets its own MCP server. SOMA should:
1. **Consume** existing medical MCP servers (healthcare-mcp-public for knowledge, mcp-slicer for 3D processing)
2. **Build** a SOMA-specific MCP server that exposes anatomy models, bilingual terms, and educational content
3. **Bundle** MCP client capability into the SOMA app so it can call these servers

## Integration Priority
1. **healthcare-mcp-public** — easiest win, Docker deploy, comprehensive medical data
2. **mcp-slicer** — highest impact if mesh pipeline can be replaced
3. **medadapt-content-server** — aligns with educational mission


## Sources

- https://github.com/sunanhe/awesome-medical-mcp-servers
- https://github.com/Cicatriiz/healthcare-mcp-public
- https://github.com/zhaoyouj/mcp-slicer
