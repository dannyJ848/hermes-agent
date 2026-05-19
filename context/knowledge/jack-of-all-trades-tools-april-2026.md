# jack-of-all-trades-tools-april-2026

*Researched: 2026-04-04 21:11 CDT*

# Jack of All Trades: Tool Discovery Report (April 2026)

## Top 5 Tools Discovered

### 1. Kitware VolView (Score: 80/100) ⭐
- **What**: Browser-based 3D radiological DICOM viewer (TypeScript/Vue.js)
- **Repo**: github.com/Kitware/VolView (274 stars, Apache-2.0)
- **Why SOMA**: Volume rendering, DICOM ingestion, annotation UX — directly applicable to SOMA's 3D anatomy pipeline. ITK-WASM for image processing is reusable.
- **Action**: Study VolView's transfer function UI and ITK-WASM integration for SOMA's cross-section feature.

### 2. ACE-Step 1.5 (Score: 79/100) ⭐
- **What**: Open-source music generation foundation model, rivals Suno/Udio
- **Repo**: github.com/ace-step/ACE-Step-1.5 (8,500 stars, Apache-2.0)
- **Why SOMA**: Could generate background music/audio for educational anatomy content. Also relevant as an audio tool for Hermes creative workflows.
- **Action**: Evaluate for generating audio narrations or ambient music for SOMA lessons.

### 3. Healthcare MCP Server (Score: 73/100)
- **What**: MCP server with FDA drug info, PubMed, DICOM metadata, clinical trials, ICD-10, medical calculator
- **Repo**: github.com/Cicatriiz/healthcare-mcp-public (104 stars, MIT)
- **Why SOMA**: Provides structured healthcare data access. Could be used alongside BioMCP for richer medical information retrieval.
- **Action**: Test as supplementary MCP server for medical data queries.

### 4. DECODE-3DViz (Score: 65/100)
- **What**: WebGL-based LOD + chunk streaming for large-scale medical image visualization
- **Paper**: Journal of Imaging Informatics in Medicine (2025)
- **Why SOMA**: LOD and data chunk streaming techniques could optimize SOMA's mobile performance when rendering high-poly anatomy models.
- **Action**: Study the LOD approach for SOMA's mobile rendering pipeline.

### 5. Slice Viewer (Score: 57/100)
- **What**: Minimal WebGL viewer for CT/MRI exploration in 3 planes (React)
- **Repo**: github.com/vangelov/slice-viewer (22 stars)
- **Why SOMA**: Clean reference implementation for cross-sectional viewing of medical scans alongside 3D anatomy models.
- **Action**: Study code patterns for SOMA's cross-section feature implementation.

## Skills Created
1. `volview-dicom` (mcp/) — Kitware VolView DICOM viewer skill
2. `ace-step` (mlops/) — ACE-Step 1.5 music generation skill

## Key Insight
The medical imaging web ecosystem is maturing rapidly. Kitware's ITK-WASM approach (running industrial VTK/ITK in browser via WebAssembly) is the most promising technique for SOMA's cross-section and DICOM integration. The LOD + chunk streaming from DECODE-3DViz addresses SOMA's mobile performance bottleneck directly.


## Sources

- https://github.com/ace-step/ACE-Step-1.5
- https://github.com/Kitware/VolView
- https://github.com/Cicatriiz/healthcare-mcp-public
- https://link.springer.com/article/10.1007/s10278-025-01430-9
- https://github.com/vangelov/slice-viewer
