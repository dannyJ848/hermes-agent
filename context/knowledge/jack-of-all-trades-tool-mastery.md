# jack-of-all-trades-tool-mastery

*Researched: 2026-04-01 23:40 CDT*

# Jack of All Trades: Tool Mastery Reference
> Comprehensive guide to every tool domain an autonomous agent should master.
> Updated: April 2026

---

## 1. AI/ML Agent Frameworks

| Framework | ★ Stars | Lang | Best For | Install |
|-----------|---------|------|----------|---------|
| LangGraph | 15K+ | Py/JS | Stateful graph workflows, enterprise | `pip install langgraph` |
| CrewAI | 25K+ | Py | Multi-agent role-based teams | `pip install crewai` |
| AutoGen | 40K+ | Py | Microsoft multi-agent conversations | `pip install autogen-agentchat` |
| OpenAI Agents SDK | 8K+ | Py | Official OpenAI, handoffs | `pip install openai-agents` |
| Google ADK | 18K+ | Py | Native Gemini, multi-agent | `pip install google-adk` |
| Pydantic AI | 10K+ | Py | Type-safe, production-ready | `pip install pydantic-ai` |
| DSPy | 25K+ | Py | Programming not prompting, auto-optimize | `pip install dspy` |
| Mastra | 12K+ | TS | TypeScript-first agents | `npm install mastra` |
| Dify | 130K+ | Py/TS | Low-code agent platform | Docker deploy |

**For SOMA**: LangGraph for clinical workflows, DSPy for prompt optimization, Pydantic AI for type-safe medical data handling.

---

## 2. LLM Inference & Serving

| Tool | ★ Stars | Best For | Hardware | Install |
|------|---------|----------|----------|---------|
| Ollama | 130K+ | Local LLM serving, easiest setup | CPU/GPU/Mac | `curl -fsSL https://ollama.com/install.sh \| sh` |
| vLLM | 45K+ | High-throughput production serving | GPU only | `pip install vllm` |
| llama.cpp | 75K+ | CPU/Apple Silicon inference | CPU/GPU | `make && ./main` |
| LM Studio | 50K+ | GUI for local models | CPU/GPU/Mac | Desktop app |
| LocalAI | 30K+ | OpenAI-compatible local API | CPU/GPU | Docker |

**For SOMA**: Ollama on Mac Mini for local Qwen3.5 context compression (witcheer pattern). vLLM for production GPU serving.

---

## 3. Vector Databases

| DB | ★ Stars | Type | Best For | Install |
|----|---------|------|----------|---------|
| Qdrant | 22K+ | Purpose-built | High-performance, Rust, filtering | Docker / `pip install qdrant-client` |
| Chroma | 18K+ | Embedded | Quick prototyping, Python-native | `pip install chromadb` |
| Weaviate | 15K+ | Purpose-built | Multi-modal, GraphQL | Docker |
| Milvus | 32K+ | Purpose-built | Billion-scale, enterprise | Docker / `pip install pymilvus` |
| pgvector | 15K+ | Extension | Already using Postgres | `CREATE EXTENSION vector` |
| LanceDB | 6K+ | Embedded | Serverless, multi-modal | `pip install lancedb` |

**For SOMA**: Qdrant (already in use via omem). Chroma for rapid prototyping of medical document search.

---

## 4. Browser Automation & Computer Use

| Tool | ★ Stars | Type | Best For |
|------|---------|------|----------|
| Stagehand (Browserbase) | 15K+ | AI+Playwright | Hybrid deterministic+AI browser automation |
| browser-use | 50K+ | Python agent | Autonomous browser navigation |
| Playwright MCP | 5K+ | MCP server | Direct browser control from agents |
| Camofox | 2K+ | Anti-detect | Bypass bot detection |
| Skyvern | 15K+ | Visual | Form filling, visual agents |

**For SOMA**: Stagehand for reliable hybrid automation, browser-use for exploratory browsing of medical resources.

---

## 5. Medical & Bioinformatics Tools

| Tool | ★ Stars | Function | Access |
|------|---------|----------|--------|
| BioMCP | 481 | PubMed/ClinicalTrials/FDA/g:Profiler | `biomcp serve` (INSTALLED) |
| Healthcare MCP | 104 | FDA drugs/ICD-10/medRxiv/DICOM | MCP server |
| M3 (cBioPortal) | 70 | MIMIC-IV clinical analytics | DuckDB/BigQuery |
| MONAI | 6K+ | Medical imaging deep learning (PyTorch) | `pip install monai` |
| OHIF Viewer | 3K+ | Web DICOM viewer (React) | npm deploy |
| dwv (DICOM Web Viewer) | 500+ | JS/HTML5 DICOM viewer | npm |
| 3D Slicer | 8K+ | Desktop medical image analysis | Desktop app |
| ITK | 1.5K+ | Medical image processing (C++) | `pip install itk` |
| FHIR.js | 300+ | HL7 FHIR client for JS | `npm install fhir.js` |
| OpenFDA API | N/A | Drug safety, adverse events | REST API (free) |

**For SOMA**: BioMCP (active). MONAI for medical image analysis. OHIF/dwv for DICOM in browser. FHIR.js for interoperability. OpenFDA for drug safety data.

---

## 6. 3D Graphics & Anatomy Visualization

| Tool | ★ Stars | Function | SOMA Relevance |
|------|---------|----------|----------------|
| Three.js | 105K+ | Web 3D engine | Core of SOMA's 3D body viewer |
| React Three Fiber | 30K+ | React bindings for Three.js | SOMA's component architecture |
| z-anatomy | 500+ | Open-source 3D anatomy atlas | Anatomy models (.blend files) |
| BodyParts3D | N/A | 3D anatomical structure DB | Anatomical model data |
| OpenAnatomy | N/A | Free anatomy atlas | Educational content |
| Blender Python API | N/A | Scripted 3D modeling | Creating/editing anatomy models |
| D3.js | 110K+ | Data visualization | Medical data charts |
| deck.gl | 12K+ | Geospatial visualization | Health data maps |
| Gaussian Splatting | 15K+ | 3D from images | Potential body scanning |

**For SOMA**: React Three Fiber + z-anatomy models. Blender Python API for custom anatomy creation.

---

## 7. Speech & Audio Tools

### Speech-to-Text (STT)
| Tool | ★ Stars | Best For | Medical Use |
|------|---------|----------|-------------|
| Whisper (OpenAI) | 80K+ | General STT, multilingual | Patient dictation, bilingual EN/ES |
| Whisper Large V3 Turbo | - | 6x faster than V3 | Real-time medical transcription |
| Whisper-Medusa | 2K+ | Medical-specialized STT | Clinical terminology accuracy |
| Deepgram | 5K+ | Real-time API STT | Fast production transcription |
| Vosk | 8K+ | Offline STT | Privacy-sensitive medical use |

### Text-to-Speech (TTS)
| Tool | ★ Stars | Best For | Medical Use |
|------|---------|----------|-------------|
| ElevenLabs | API | Most natural voices | Patient education audio |
| WhisperSpeech | 5K+ | Open-source TTS (inverse Whisper) | Free bilingual voice |
| Bark (Suno) | 40K+ | Expressive TTS | Multi-language support |
| Coqui TTS | 35K+ | Production TTS | Custom medical voice models |
| Chatterbox (Resemble) | 3K+ | Low-latency production TTS | Real-time medical narration |

### Music & Audio Generation
| Tool | ★ Stars | Function |
|------|---------|----------|
| Suno API | API | AI music generation |
| AudioCraft/MusicGen (Meta) | 25K+ | Open-source music gen |
| FFmpeg | N/A | Audio/video processing (universal) |
| heartmula | 100+ | Open-source music (Hermes skill exists) |

**For SOMA**: Whisper V3 Turbo for bilingual patient dictation. WhisperSpeech for free TTS in EN/ES. FFmpeg for audio processing.

---

## 8. Video & Animation Tools

| Tool | ★ Stars | Function | SOMA Use |
|------|---------|----------|----------|
| Remotion | 22K+ | Programmatic video with React | Medical education videos |
| FFmpeg | N/A | Video processing | Universal media tool |
| MoviePy | 13K+ | Python video editing | Automated video creation |
| Manim | 75K+ | Math/science animations | Medical concept animations |
| Lottie | 17K+ | UI animations | SOMA interface animations |
| D-ID / HeyGen | API | Talking head videos | Patient education avatars |
| Open Fern | New | Open-source AI video studio | 2026 tool to watch |
| Stable Video Diffusion | 15K+ | Image-to-video | Medical visualization |

**For SOMA**: Remotion for React-based medical education videos. Manim for concept animations. Lottie for UI polish.

---

## 9. MCP Server Ecosystem

Top MCP servers by category (from best-of-mcp-servers, 450+ servers, 920K total stars):

**Development**: FastMCP (24K), GitHub MCP, Filesystem MCP
**Database**: Chroma MCP, Qdrant MCP, PostgreSQL MCP  
**Browser**: Playwright MCP, Puppeteer MCP, Browserbase MCP
**Communication**: Slack MCP, Discord MCP, Telegram MCP
**Medical**: BioMCP (481), Healthcare MCP (104), M3 (70)
**Search**: Firecrawl MCP, SearXNG MCP, Brave Search MCP
**Data**: Pandas MCP, CSV MCP, Google Sheets MCP

**For SOMA**: BioMCP (active). Add Healthcare MCP and Qdrant MCP next.

---

## 10. Priority Skills to Create

Based on relevance scoring (Novelty + SOMA Utility + Community + Integration Ease):

| Priority | Tool | Score | Action |
|----------|------|-------|--------|
| P0 | Whisper STT/TTS | 92 | Create skill for bilingual medical transcription |
| P0 | MONAI medical imaging | 88 | Create skill for DICOM processing |
| P1 | React Three Fiber anatomy | 85 | Expand anatomy-3d-viewer skill |
| P1 | FHIR/HL7 integration | 82 | Create skill for healthcare interoperability |
| P1 | OpenFDA API | 80 | Create skill for drug safety queries |
| P2 | Remotion video gen | 78 | Create skill for medical education videos |
| P2 | Manim animations | 75 | Create skill for medical concept animations |
| P2 | Stagehand browser | 75 | Create skill for hybrid browser automation |
| P3 | DSPy prompt optimization | 72 | Integrate with hermes-dojo for self-evolution |
| P3 | Ollama local models | 70 | Create skill for local inference fallback |

---

## 11. Infrastructure Status

| Component | Status | Endpoint |
|-----------|--------|----------|
| omem (shared memory) | ACTIVE | http://localhost:8080 |
| TeamMCP (squad coord) | ACTIVE | http://localhost:3100 |
| BioMCP (medical data) | ACTIVE | MCP server (5 tools) |
| SOMA Dojo cron | ACTIVE | 03:00 daily |
| Jack of Trades cron | ACTIVE | 09:00, 21:00 daily |
| X Scanner cron | ACTIVE | 09:00, 15:00, 21:00 |


## Sources

- https://www.firecrawl.dev/blog/best-open-source-agent-frameworks
- https://www.firecrawl.dev/blog/best-vector-databases
- https://github.com/caramaschiHG/awesome-ai-agents-2026
- https://github.com/tolkonepiu/best-of-mcp-servers
- https://encore.dev/articles/best-vector-databases
- https://vapi.ai/blog/medical-speech-to-text-software
- https://encord.com/blog/best-dicom-viewers/
- https://github.com/kakoni/awesome-healthcare
