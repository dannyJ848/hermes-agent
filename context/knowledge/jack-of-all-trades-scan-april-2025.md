# jack-of-all-trades-scan-april-2025

*Researched: 2026-04-07 21:10 CDT*

# Jack of All Trades Tool Scan — April 2025

## Top 5 Tools Discovered

### 1. ACE-Step 1.5 (Score: 81/100)
- **Repo**: ace-step/ACE-Step-1.5 | 8,621⭐ | Python | MIT
- Open-source music foundation model rivaling Suno/Udio. Runs locally on consumer hardware. Text-to-music, lyrics-to-song, style transfer.
- **Skill already exists**: `ace-step`

### 2. Ossium — WebGPU Volume Renderer (Score: 80/100)
- **Repo**: fraserlove/ossium | 13⭐ | TypeScript | MIT
- Pure WebGPU volume rendering for 3D medical imaging in browser. Directly relevant to SOMA's rendering pipeline.
- **Skill already exists**: `ossium-webgpu-volume-renderer`

### 3. DWV — DICOM Web Viewer (Score: 75/100)
- **Repo**: ivmartel/dwv | 1,808⭐ | JavaScript | GPL-3.0
- Zero-footprint DICOM viewer library. Pure HTML5/JS. Embeddable medical image viewing.
- **Skill created**: `dwv-dicom-web-viewer`

### 4. lastmile-ai/mcp-agent (Score: 74/100)
- **Repo**: lastmile-ai/mcp-agent | 8,204⭐ | Python | Apache-2.0
- Composable MCP agent patterns: map-reduce, orchestrator, evaluator-optimizer, router.
- **Skill already exists**: `mcp-agent-workflows`

### 5. BioLens (Score: 64/100)
- **Repo**: felix-ops/bio-lens | 18⭐ | TypeScript
- Babylon.js volumetric medical scan viewer. Browser-native DICOM import with transfer functions.
- Interesting approach but Three.js (SOMA's stack) differs from Babylon.js. Concept transfer useful.

## Other Notable Finds
- **Google MedGemma**: Open multimodal LLM for medical text/image comprehension. Built on Gemma 3. Already tracked in `medgemma-medical-vlm` skill.
- **AgenticHealthAI/Awesome-AI-Agents-for-Healthcare**: 812⭐ curated list of healthcare AI agent papers and projects. Good research resource.
- **OHIF Viewer 3.9**: Advanced segmentation with Cornerstone 3D 2.0. Major medical imaging viewer.
- **Kitware VolView + NVIDIA Clara**: Integration of AI models into browser-native imaging. Relevant for SOMA's AI-assisted diagnosis roadmap.

## Cross-Domain Insight
WebGPU volume rendering (Ossium) + FHIR patient records (Medplum) + bilingual medical terms (SOMA) creates a unique stack not found in any existing medical app. The gap between consumer 3D anatomy apps (Complete Anatomy) and clinical tools (OHIF) is SOMA's blue ocean.


## Sources

- https://github.com/ace-step/ACE-Step-1.5
- https://github.com/fraserlove/ossium
- https://github.com/ivmartel/dwv
- https://github.com/lastmile-ai/mcp-agent
- https://github.com/felix-ops/bio-lens
- https://github.com/AgenticHealthAI/Awesome-AI-Agents-for-Healthcare
