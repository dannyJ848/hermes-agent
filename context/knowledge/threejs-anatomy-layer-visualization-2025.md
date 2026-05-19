# threejs-anatomy-layer-visualization-2025

*Researched: 2026-04-06 00:23 CDT*

# Three.js Anatomy Layer Visualization — Community Intelligence (Dec 2025 - Mar 2026)

## Source: Three.js Discourse Forum Thread
**URL:** https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813

## Key Insights for SOMA

### 1. Validated Architecture: Layer-Based Anatomy in Three.js
A student (Taron Holikyan) proposed EXACTLY what SOMA builds: toggle anatomical layers (skin, muscles, skeleton, veins, organs, brain/nervous system) with transparency, highlighting, and click-to-info. This validates the SOMA approach as the standard architecture for anatomy viewers.

### 2. Recommended Pipeline: Blender → glTF → Three.js
- **phil_crowther** (experienced member): Blender models exported as .glb, imported via GLTFLoader
- **Z-Anatomy** confirmed as the go-to free model source for Blender
- YouTube tutorials exist for the Blender → Three.js workflow

### 3. Competitive Landscape
- **zygotbody.com** — existing commercial anatomy viewer (no source code)
- Multiple forum members working on similar projects
- "3D Human Anatomy Showcase" thread has 6125 views — high interest
- Another thread "Layer-Based Interactive 3D Human Anatomy" from Dec 2025

### 4. Technical Challenges Identified (matching SOMA's)
- Performance with complex multi-layer models
- Real-time layer switching (show/hide systems)
- Transparency per layer
- Click-to-info on individual organs
- Memory management for large anatomical datasets

### 5. SOMA Differentiation Opportunities
- Most projects are student/diploma level — no mobile-optimized bilingual medical viewer exists
- No one mentions EN/ES bilingual terminology
- No mention of iOS-optimized rendering (WKWebView)
- SSS shaders for realistic tissue appearance not discussed
- FHIR/medical data integration not mentioned by any competitor

## Actionable for SOMA
- Use Z-Anatomy as Blender source (already planned)
- Export pipeline: Blender → glTF → Three.js GLTFLoader (confirmed best practice)
- Layer toggling via Three.js Group visibility (standard approach)
- SOMA's mobile + bilingual + SSS shader stack is genuinely unique in this space

## Sources

- https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813
- https://zygotbody.com
