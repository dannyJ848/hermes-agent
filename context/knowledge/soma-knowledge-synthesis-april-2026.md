# soma-knowledge-synthesis-april-2026

*Researched: 2026-04-03 06:05 CDT*

# Knowledge Synthesis: SOMA Competitive & Technology Landscape (April 2026)

## Connections Across Sessions

### Thread 1: Segmentation Pipeline
- **Session 1** (5AM Apr 3): TotalSegmentator → VTK → glTF pipeline validated
- **Session 2** (6AM Apr 3): SAM2 zero-shot segmentation (EPFL) offers interactive alternative
- **Connection**: SAM2 + TotalSegmentator complement each other. TotalSegmentator for 104 pre-defined structures, SAM2 for user-prompted arbitrary structures. Pipeline becomes: DICOM → TotalSegmentator (batch) + SAM2 (interactive) → VTK → glTF → Three.js

### Thread 2: Medical Data Standards  
- **Session 1** (4AM Apr 3): FHIR/HL7 integration strategy, ImagingStudy resource
- **Session 2** (6AM Apr 3): Materialise reports 500+ hospitals using 3D planning, interoperability critical
- **Connection**: FHIR compliance is becoming a requirement, not a nice-to-have. Hospitals expect integration with existing systems. SOMA needs FHIR ImagingStudy support for clinical adoption.

### Thread 3: Competitive Positioning
- **Avatar Medical**: Clinical/surgical, no-segmentation, glasses-free 3D, FDA-cleared → $$
- **Anatomage**: Education, real cadaver data, proprietary hardware → $$
- **Materialise**: Surgical planning, 500+ hospitals, case management → $$$
- **SOMA**: Education, mobile-first, bilingual EN/ES, open-source, interactive → Free/Open

**SOMA's moat**: No competitor targets Spanish-speaking uninsured communities with free, mobile 3D anatomy. The bilingual angle is unique.

### Thread 4: Agent Infrastructure
- **Hermes updates**: ACP MCP registration, pluggable memory providers, per-turn recovery
- **OpenClaw**: 210K stars, self-extending skills
- **MCP ecosystem**: 500+ servers, enterprise adoption
- **Connection**: SOMA's agent infrastructure (for interactive tutoring) should leverage MCP for extensibility. Hermes' new ACP integration means SOMA's dev environment can use MCP tools natively.

## Prioritized Action Items for SOMA

1. **Prototype SAM2 integration** — highest impact, interactive segmentation differentiator
2. **FHIR ImagingStudy support** — clinical adoption requirement
3. **Mobile 3D performance** — Three.js/WebGPU optimization (Triangle budgets, LOD)
4. **Bilingual content** — Expand EN/ES terminology beyond 45 terms
5. **MCP extensibility** — Design SOMA's interactive tutor as an MCP tool

## Monthly Goal Progress (April 2026)
- Knowledge findings: 7/30 (on track)
- SOMA features: 0/5 (need to start coding at 9AM)
- Skills: 1 update/10 (need more)
- Research: 8/50 papers/articles (good pace)
- Ecosystem tools: 10+/20 identified
- Cron health: 95%+ maintained ✅


## Sources

- session:5am-apr3
- session:6am-apr3
- session:4am-apr3
- ecosystem-scan-2026-04-03-morning
- sam2-zero-shot-3d-ct-segmentation
