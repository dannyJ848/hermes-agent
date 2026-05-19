# 3d-visual-grounding-anatomy-2025

*Researched: 2026-04-07 11:50 CDT*

# 3D Visual Grounding & Medical Rendering — Research Summary (Apr 2025)

## 3D Visual Grounding
- **Awesome-3D-Visual-Grounding** (GitHub, 273 stars): Curated list of T-3DVG (Text-guided 3D Visual Grounding) papers. Goal: locate specific objects in 3D scenes from language queries.
- **ViewSRD** (ICCV 2025): "3D Visual Grounding via Structured Multi-View Decomposition" — decomposes 3D grounding into structured multi-view reasoning. Key innovation: disentangling complex 3D scenes into manageable view-specific grounding tasks.
- **Application to SOMA**: These techniques map directly to Three.js raycasting + element picking. In SOMA, we need to ground user language queries ("show me the temporalis muscle") to 3D mesh coordinates. Multi-view decomposition could improve accuracy on complex anatomical structures where single-view raycasting fails.

## Real-Time Subsurface Scattering (SIGGRAPH 2025)
- **Novel hybrid SSS method** presented at SIGGRAPH 2025 Advances in Real-Time Rendering. Approaches path-traced quality at real-time speeds. Designed for current-gen game pipelines.
- Key insight: hybrid method combining screen-space techniques with precomputed scattering profiles.
- **Application to SOMA**: Human tissue is one of the hardest materials to render convincingly — skin, muscle, organs all exhibit strong subsurface scattering. This SIGGRAPH 2025 technique could be adapted for WebGL/WebGPU to make SOMA's anatomical models look dramatically more realistic.

## Multimodal Generative AI for 3D Medical Imaging (Nature, May 2025)
- Paper proposes treating 3D medical images (CT/MRI) as video sequences for multimodal video-text models.
- Applications: automated reporting, case retrieval, education.
- Key insight: 3D medical images have synergistic information across slices, metadata, and world model priors.
- **Application to SOMA**: The video-as-3D paradigm could inform how SOMA presents cross-sectional views — treating anatomy exploration as a "video" where the user scrubs through layers, with AI assistance at each level.

## Khronos "3D on the Web" 2026 Event
- GDC-adjacent event covering glTF, WebGL, WebGPU, and interactive 3D on the web. Directly relevant to SOMA's web-based rendering stack.


## Sources

- https://github.com/liudaizong/Awesome-3D-Visual-Grounding
- https://openaccess.thecvf.com/content/ICCV2025/papers/Huang_ViewSRD_3D_Visual_Grounding_via_Structured_Multi_View_Decomposition_ICCV_2025_paper.pdf
- https://advances.realtimerendering.com/s2025/
- https://www.nature.com/articles/s41746-025-01649-4
- https://www.khronos.org/events/3d-on-the-web-2026
