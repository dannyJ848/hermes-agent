# Jack of All Trades Scan — April 2026 Tool Discovery

*Researched: 2026-04-04 09:08 CDT*

# Tool Discovery Report — April 4, 2026

## Top 5 Tools Discovered

### 1. 🥇 Stanford Merlin — CT Vision-Language Model (Score: 82/100)
- **Repo**: github.com/StanfordMIMI/Merlin (353 ⭐)
- **What**: 3D VLM for computed tomography, published Nature 2026
- **Novelty**: 20/25 — First CT-specific VLM with EHR+report pretraining
- **SOMA Utility**: 22/25 — Could power diagnostic imaging education
- **Traction**: 15/25 — 353 stars, Stanford MIMI backed, Nature publication
- **Integration**: 25/25 — `pip install merlin-vlm`, Python, MIT license
- **Action**: Skill created (`merlin-ct-vlm`)

### 2. 🥈 Fish Speech S2 — SOTA Open Source TTS (Score: 78/100)
- **Repo**: github.com/fishaudio/fish-speech (29K ⭐)
- **What**: Best open-source TTS, 80+ languages, outperforms closed-source
- **Novelty**: 18/25 — DualAR architecture is innovative
- **SOMA Utility**: 20/25 — Bilingual EN/ES critical for SOMA
- **Traction**: 25/25 — 29K stars, massive community
- **Integration**: 15/25 — Requires GPU, more complex than Chatterbox
- **Note**: Chatterbox already covers this niche (Turbo is lighter)

### 3. 🥉 Google genai-toolbox — MCP for Healthcare APIs (Score: 75/100)
- **Repo**: github.com/googleapis/genai-toolbox (13.7K ⭐)
- **What**: MCP server connecting AI agents to Cloud Healthcare API (FHIR, DICOM, HL7v2)
- **Novelty**: 16/25 — Pre-built healthcare MCP tools
- **SOMA Utility**: 24/25 — Direct FHIR/DICOM access for medical data
- **Traction**: 20/25 — 13.7K stars, Google backed
- **Integration**: 15/25 — Requires GCP account and healthcare API setup
- **Note**: Best for production FHIR/DICOM integration; BioMCP covers local needs

### 4. OpenClaw — Web Automation Agent (Score: 62/100)
- **Repo**: github.com/openclaw/openclaw (347K ⭐)
- **What**: Personal AI assistant, any OS/platform
- **Novelty**: 10/25 — Another agent framework
- **SOMA Utility**: 8/25 — Indirect value only
- **Traction**: 25/25 — 347K stars (!)
- **Integration**: 19/25 — TypeScript, MIT

### 5. Interactive 3D Human Heart — Three.js (Score: 45/100)
- **Repo**: github.com/simonreisinger/Interactive-3D-Human-Heart-Visualization (12 ⭐)
- **What**: Three.js heart visualization for education
- **Novelty**: 12/25 — Layer-based anatomy exploration
- **SOMA Utility**: 18/25 — Similar to SOMA's own 3D work
- **Traction**: 3/25 — Only 12 stars
- **Integration**: 12/25 — Could study techniques but small codebase

## Notable Mention: GNAP (Git-Native Agent Protocol)
- Protocol for agent coordination via git (4 JSON files, no server)
- Currently RFC/proposal stage, promoted via GitHub issues across major repos
- Interesting concept but not yet a working tool — watch for future development

## Skills Created
- `merlin-ct-vlm` — Full skill with installation, usage, SOMA integration notes

## Recommended Next Actions
1. Monitor Fish Speech S2 releases — if Spanish quality improves, consider switch from Chatterbox
2. Set up Google genai-toolbox MCP for FHIR access when SOMA needs production healthcare data
3. Watch Stanford Merlin for multimodal extensions (X-ray, MRI support)
4. Skip OpenClaw — not relevant to SOMA's medical education mission


## Sources

- https://github.com/StanfordMIMI/Merlin
- https://github.com/fishaudio/fish-speech
- https://github.com/googleapis/genai-toolbox
- https://github.com/openclaw/openclaw
- https://github.com/simonreisinger/Interactive-3D-Human-Heart-Visualization
- https://docs.cloud.google.com/healthcare-api/docs/tutorials/pre-built-tools-with-mcp-toolbox
- https://flowith.io/blog/10-best-open-source-agent-projects-github-2026
- https://www.siliconflow.com/articles/en/best-open-source-music-generation-models
