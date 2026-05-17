# ecosystem-scan-2026-04-03-morning

*Researched: 2026-04-03 06:01 CDT*

# Morning Ecosystem Scan — April 3, 2026

## AI Agent Landscape (GitHub Trending)

### OpenClaw — Breakout Star of 2026
- Fastest-growing open-source project in GitHub history: 9K → 210K+ stars
- Created by Peter Steinberger (PSPDFKit founder)
- Personal AI assistant running entirely on local devices
- 50+ integrations (WhatsApp, Telegram, Slack, Discord, Signal, iMessage)
- Can write its own new skills (self-extending capabilities)
- Steinberger joined OpenAI on Feb 14, 2026; project transitioning to open-source foundation
- Security concerns: broad permissions, skill repository lacks rigorous vetting
- **SOMA relevance**: Local-first architecture pattern is similar to Hermes. Self-extending skills is a pattern worth studying.

### Key AI Infrastructure Repos
- **n8n** — Visual workflow automation with native AI/LangChain integration, 400+ integrations, self-hostable
- **Langflow** — Low-code drag-and-drop for RAG and multi-agent flows
- **Dify** — Production-ready agentic workflow platform with MCP support

## MCP Ecosystem

### State of MCP (April 2026)
- 500+ public MCP servers available
- Supported by Anthropic, OpenAI, and Google DeepMind
- Transport Working Group evolving beyond Streamable HTTP for enterprise-scale

### Top 15 MCP Servers (K2view directory)
1. K2view — Enterprise data, entity-based real-time access
2. Vectara — Semantic search, RAG-ready
3. Zapier — 6,000+ app automations
4. Notion — Workspace data, pages, tasks
5. (others cut off)

### MCP Security Concerns
- Tunneling pattern emerging for securing MCP servers (instatunnel article)
- Need proper auth/data governance for enterprise deployments

## Medical 3D / Anatomy Competitive Landscape

### Avatar Medical — Direct SOMA Competitor
- Founded 2020, from Institut Curie and Institut Pasteur research
- CT/MRI → lifelike 3D avatars instantly, **without segmentation**
- FDA-cleared for preoperative planning
- **Eonis Vision** — Glasses-free 3D display with Barco, CES 2026 Innovation Honoree
- Partnership with Dell, NVIDIA, Barco
- Commercial availability Q2 2026 (after FDA clearance expansion)
- Clinical applications: Neurosurgery, ENT, Orthopedic, Oncology, Cardiovascular, Urology
- **Key differentiator**: No segmentation needed — instant volumetric rendering
- **SOMA relevance**: Avatar Medical targets clinical/surgical use. SOMA's niche is medical education + bilingual access. Different market segment but technology overlaps significantly.

### Materialise — 3D Surgical Planning Trends 2026
- 500+ hospitals now using 3D planning workflows
- 5 key trends:
  1. From standalone 3D printing → comprehensive surgical planning platforms
  2. XR (AR/VR) gaining clinical traction — especially congenital heart disease, oncology
  3. Case management as backbone (governance, traceability)
  4. AI automating anatomical segmentation — 30% time reduction
  5. Shift from "good enough" volume rendering → high-fidelity surface modeling
- **SOMA relevance**: AI-automated segmentation validates TotalSegmentator approach. Surface modeling demand aligns with SOMA's mesh pipeline.

## Anatomage
- Advancing real human cadaver datasets for medical education
- New generation of 3D anatomy models based on real human data
- **SOMA relevance**: Direct education competitor. SOMA differentiates with open-source, mobile-first, bilingual.

## Key Takeaways for SOMA
1. Avatar Medical's instant no-segmentation approach is a threat — SOMA should explore volume rendering fallback
2. AI segmentation is now standard (30% time savings) — validates our TotalSegmentator pipeline
3. MCP ecosystem maturing rapidly — 500+ servers, enterprise adoption growing
4. OpenClaw's self-extending skills pattern is worth studying for Hermes/SOMA
5. XR integration in clinical settings is accelerating — consider ARKit support for SOMA iOS


## Sources

- https://blog.bytebytego.com/p/top-ai-github-repositories-in-2026
- https://www.avatarmedical.ai/press-kit
- https://www.k2view.com/blog/awesome-mcp-servers
- https://www.materialise.com/en/inspiration/articles/5-transformative-trends-3d-virtual-surgical-planning-hospitals-2026
- https://decodethefuture.org/en/what-is-mcp-model-context-protocol/
