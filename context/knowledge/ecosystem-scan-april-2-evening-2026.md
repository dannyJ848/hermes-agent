# ecosystem-scan-april-2-evening-2026

*Researched: 2026-04-02 22:13 CDT*

# Ecosystem Scan: April 2, 2026 Evening

*Scanned: 2026-04-02 22:15 CDT*

## Papers Discovered

### 1. Subsurface Scattering for 3D Gaussian Splatting
- **arXiv:** 2408.12282v2 (Oct 2024)
- **Authors:** Dihlmann, Majumdar, Engelhardt, Braun, Lensch
- **Key Innovation:** Extends 3D Gaussian Splatting with volumetric SSS representation. Decomposes scene into explicit surface (3D Gaussians + spatially varying BRDF) and implicit volumetric scattering. Learned incident light field for shadowing.
- **SOMA Relevance:** HIGH — This is exactly the SSS technique SOMA needs. The "material editing, relighting and novel view synthesis at interactive rates" directly applies to anatomy visualization where tissue type determines scatter parameters. Could replace or complement our TSL-based SSS approach.

### 2. 3D Cardiac Anatomy Generation Using Mesh Latent Diffusion
- **arXiv:** 2508.14122 (Aug 2025)
- **Authors:** Mozyrska, Beetz, Melas-Kyriazi, Grau, Banerjee, Bueno-Orovio
- **Key Innovation:** MeshLDM — Latent Diffusion Model for generating diverse 3D cardiac meshes. Captures end-diastolic and end-systolic phases with only 2.4% deviation from population mean.
- **SOMA Relevance:** MEDIUM — Could generate synthetic cardiac anatomy variants for education content. Shows pathology-specific anatomy generation (acute myocardial infarction patients). Potential for SOMA's "My Conditions" mode where patient-specific anatomy is visualized.

### 3. Coordinated 2D-3D Visualization of Volumetric Medical Data in XR
- **arXiv:** 2506.22926
- **Key Innovation:** Multimodal interaction for XR medical visualization with coordinated 2D/3D views.
- **SOMA Relevance:** MEDIUM — Relevant for SOMA's future XR mode. The coordinated 2D slice + 3D volume interaction pattern is exactly what medical education needs.

## MCP Healthcare Ecosystem (Rapidly Growing)

### Keragon (MCP for Healthcare)
- **Raised:** $10.5M total funding
- **Features:** 300+ healthcare integrations via MCP, SOC2 Type II + HIPAA compliant
- **Relevance:** Could provide MCP servers for EHR integration in SOMA's "My Health" mode

### Wolters Kluwer — MCP + Agentic Healthcare
- Article explores how MCP standardizes AI agent connections to clinical resources
- Focus on security, reliability, and clinical decision support
- **Relevance:** Validates SOMA's MCP-based architecture approach

### Ketryx MCP Beta
- Bringing medical device software development into AI workflows via MCP
- **Relevance:** Could be used for SOMA's regulatory compliance workflows

## Key Takeaway
MCP for healthcare is becoming an industry standard. SOMA's architecture (BioMCP + FHIR MCP) is well-aligned. The 3D Gaussian Splatting + SSS paper offers a potential rendering upgrade path beyond TSL-based SSS.


## Sources

- https://arxiv.org/abs/2408.12282
- https://arxiv.org/abs/2508.14122
- https://www.keragon.com/blog/best-mcp-servers
- https://www.wolterskluwer.com/en/expert-insights/exploring-mcp-how-model-context-protocol-supports-the-future-of-agentic-healthcare
