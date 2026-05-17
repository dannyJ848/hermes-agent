# medical-mcp-servers-ecosystem-2026

*Researched: 2026-04-07 13:32 CDT*

# Medical MCP Servers Ecosystem (April 2026)

## Key Servers Relevant to SOMA

### 3D Medical Imaging
- **mcp-slicer** (zhaoyouj/mcp-slicer) — Connects 3D Slicer to MCP clients like Claude. Enables direct control of 3D Slicer for medical image analysis. **Directly relevant to SOMA's 3D anatomy viewer.**
- **dicom-mcp** (ChristianHinge/dicom-mcp) — DICOM interactions via MCP
- **fluxinc/dicom-mcp-server** — DICOM connectivity testing

### Healthcare Data
- **agentcare-mcp** (Kartha-AI) — FHIR data + EMR integration (Cerner, Epic). Could wire SOMA to real patient data.
- **medical-mcp** (chris-lovejoy) — NICE guidelines access via MCP
- **Medical_calculator_MCP** — Medical calculations via MCP

### Research
- **mcp-simple-pubmed** — PubMed via Entrez API
- **pubmedmcp** — PubMed search/fetch
- **bio-mcp** — Protein structure analysis
- **medrxiv-mcp-server** — medRxiv preprints

## Action Items for SOMA
1. Evaluate mcp-slicer for 3D Slicer integration — could enable professional-grade medical imaging
2. Consider agentcare-mcp for FHIR compliance in SOMA's data layer
3. The medical MCP ecosystem is growing rapidly — monitor this list monthly

## Source
- https://github.com/sunanhe/awesome-medical-mcp-servers


## Sources

- https://github.com/sunanhe/awesome-medical-mcp-servers
- https://github.com/zhaoyouj/mcp-slicer
- https://github.com/Kartha-AI/agentcare-mcp
