---
name: mcp
version: 2.0
description: Model Context Protocol (MCP) skills — category umbrella covering MCP server setup, healthcare/medical integrations, DICOM/FHIR viewers, and agent workflows.
trigger: When working with MCP servers, Model Context Protocol, healthcare data access, medical imaging, FHIR, DICOM, or MCP-native agent workflows.
---

# MCP Skills

## Healthcare MCP Servers

### Healthcare Data Hub (Cicatriiz/healthcare-mcp-public)

Node.js MCP server providing comprehensive healthcare data access:
- FDA Drug Lookup, PubMed Search, medRxiv, NCBI Bookshelf
- Clinical Trials, ICD-10 Codes, DICOM Metadata, Medical Calculator
- MIT Licensed, 19.4k+ visitors, Docker support
- Requires NCBI_API_KEY for full PubMed throughput

### FHIR MCP Server (the-momentum/fhir-mcp-server)

Python MCP server for Fast Healthcare Interoperability Resources:
- Natural language queries to EHR data (Epic, Cerner, MEDITECH)
- Patient lookup, observations, medications, conditions, allergies, documents
- MIT license, Docker support, public test servers available
- Config: `FHIR_BASE_URL` + `FHIR_AUTH_TOKEN`

### DICOM-MCP (ChristianHinge/dicom-mcp)

Python MCP server for DICOM medical imaging systems:
- C-FIND query, C-MOVE/C-GET retrieval from PACS/VNA
- Patient lookup, study/series/instance management, radiology report extraction
- MIT license, 88 stars, requires AE Title configuration
- Security: PHI protection, VPN/SSH tunnel for production PACS

## Medical Imaging Viewers

### DWV — DICOM Web Viewer (ivmartel/dwv)

Pure JavaScript + HTML5 zero-footprint DICOM viewer:
- 1,808 GitHub stars, GPL-3.0, client-side only
- Multi-slice navigation, window/level, zoom, pan, annotations
- Filters: threshold, sharpen, Sobel edge detection
- Mobile-friendly touch controls

### VolView (Kitware)

Open-source 3D radiological viewer in the browser:
- 274 stars, Apache-2.0, TypeScript/Vue.js
- Volume rendering with transfer functions, MPR views
- ITK/WASM backend for industrial-strength processing
- Zero server footprint — data stays local

## FHIR Platforms

### Medplum

Full-stack healthcare platform (FHIR R4):
- 2,240 stars, Apache-2.0, TypeScript monorepo
- Clinical Data Repository, FHIR API, React SDK, SMART-on-FHIR auth
- Server-side Bots (AWS Lambda for healthcare)
- Self-hostable with PostgreSQL backend

## MCP Agent Workflows

See `mcp-agent-workflows` skill for building effective agents using Model Context Protocol.

## Configuration

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  healthcare:
    command: node
    args: ["/path/to/healthcare-mcp-public/dist/index.js"]
  fhir:
    command: python
    args: [-m, fhir_mcp_server]
    env:
      FHIR_BASE_URL: "https://hapi.fhir.org/baseR4"
  dicom:
    command: dicom-mcp
    args: [--host, PACS_HOST, --port, "104"]
```

## SOMA Integration Notes

- DICOM metadata complements 3D anatomy rendering pipeline
- FHIR data connects to "My Health" branch (patient records → 3D body regions)
- ICD-10 supports bilingual medical terminology lookup
- PubMed/medRxiv enable in-app medical research
- Clinical trials support evidence-based content
- FDA drug lookup powers medication education features

## Pitfalls

- DICOM metadata tools are for metadata only, not full image rendering
- ICD-10 is US-centric; may need SNOMED CT for international use
- FHIR servers require auth in production — test with public servers first
- Patient data is sensitive — never connect to real EHR without HIPAA review
- NCBI API key needed for full PubMed throughput (1 req/sec without)
- AE Title configuration required for DICOM PACS connections
- C-MOVE vs C-GET: C-MOVE sends to third-party SCP; C-GET sends directly back
