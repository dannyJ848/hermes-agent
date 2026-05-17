# jack-of-all-trades-scan-april-2026

*Researched: 2026-04-05 09:07 CDT*

# Jack of All Trades Tool Scan — April 2026

## Top 5 Tools Discovered

### 1. Healthcare MCP Server (Cicatriiz/healthcare-mcp-public) — Score: 85/100
- **What**: Node.js MCP server with FDA drugs, PubMed, medRxiv, clinical trials, ICD-10, DICOM metadata, medical calculator
- **Stars**: 104 | **License**: MIT | **Language**: JavaScript
- **Novelty**: 20/25 — First comprehensive open-source healthcare MCP with DICOM + drug + trials + PubMed
- **SOMA Utility**: 22/25 — Directly feeds SOMA's medical content, bilingual terminology, DICOM pipeline
- **Community**: 18/25 — 19.4k visitors, active commits, PulseMCP featured
- **Integration**: 25/25 — Node.js MCP, standard protocol, Docker ready
- **Action**: Skill created (`healthcare-mcp-server`). Should wire into SOMA's MCP config.

### 2. Flexpa FHIR MCP Server (flexpa/mcp-fhir) — Score: 80/100
- **What**: TypeScript MCP server for FHIR resource interaction — Patient, Observation, Condition, etc.
- **Stars**: 65 | **License**: MIT | **Language**: TypeScript
- **Novelty**: 22/25 — Only dedicated FHIR MCP server with full CRUD operations
- **SOMA Utility**: 20/25 — FHIR integration critical for SOMA's clinical data layer
- **Community**: 15/25 — Small but focused, 12.3k visitors
- **Integration**: 23/25 — TypeScript, standard MCP protocol
- **Action**: Evaluate for SOMA patient data integration. Pair with existing fhir-mcp-server skill.

### 3. ACE-Step 1.5 Music Generation (ace-step/ACE-Step) — Score: 78/100
- **What**: Open-source music foundation model — hybrid LM planner + Diffusion Transformer
- **Stars**: 4,267 | **License**: Apache 2.0 | **Language**: Python
- **Novelty**: 23/25 — Commercial-grade music gen running on consumer hardware
- **SOMA Utility**: 15/25 — Could power audio features, educational narration, background music
- **Community**: 20/25 — Rapidly growing, 4k+ stars, active development
- **Integration**: 20/25 — Python, needs GPU. Already have skill `ace-step`
- **Action**: Already have skill. Monitor v2 updates for TTS integration possibilities.

### 4. MONAI Label (Project-MONAI/MONAILabel) — Score: 76/100
- **What**: Intelligent medical image annotation server-client system with AI-assisted labeling
- **Stars**: 828 | **License**: Apache 2.0 | **Language**: Python
- **Novelty**: 18/25 — Leading open-source medical imaging annotation framework
- **SOMA Utility**: 22/25 — Could annotate SOMA's anatomy datasets, train segmentation models
- **Community**: 20/25 — 828 stars, backed by Project MONAI (major medical AI org)
- **Integration**: 16/25 — Python-based, requires server setup, GPU recommended
- **Action**: Evaluate for SOMA's anatomy model annotation pipeline.

### 5. Google ADK Python (google/adk-python) — Score: 72/100
- **What**: Google's Agent Development Kit — code-first Python toolkit for building AI agents
- **Stars**: 18,749 | **License**: Apache 2.0 | **Language**: Python
- **Novelty**: 15/25 — Solid but competes with existing frameworks (LangChain, CrewAI)
- **SOMA Utility**: 12/25 — General agent framework, indirect value
- **Community**: 25/25 — Massive traction, Google backing
- **Integration**: 20/25 — Python, pip installable, well-documented
- **Action**: Monitor for patterns to steal. Not directly needed by SOMA.

## Emerging Ecosystem Notes

1. **OpenClaw** (210k stars) — fastest-growing OS project in GitHub history. Personal AI assistant that writes its own skills. Similar to Hermes but broader. Security concerns noted.
2. **Healthcare MCP ecosystem** is maturing rapidly — FDB launched commercial clinical decision support MCP, Keragon building healthcare MCP gateways.
3. **Three.js anatomy projects** appearing on discourse.threejs.org — layer-based interactive anatomy explorer, cranium morphometry platform. Good references for SOMA.
4. **FHIR MCP space** now has 3+ servers — Flexpa, the-momentum/fhir-mcp-server, and commercial offerings.

## Skills Created
1. `healthcare-mcp-server` — Full skill with installation, configuration, pitfalls, SOMA relevance


## Sources

- https://github.com/Cicatriiz/healthcare-mcp-public
- https://github.com/flexpa/mcp-fhir
- https://github.com/ace-step/ACE-Step
- https://github.com/Project-MONAI/MONAILabel
- https://github.com/google/adk-python
- https://www.pulsemcp.com/servers/cicatriiz-healthcare-data-hub
- https://blog.bytebytego.com/p/top-ai-github-repositories-in-2026
