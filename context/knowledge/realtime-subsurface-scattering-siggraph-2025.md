# realtime-subsurface-scattering-siggraph-2025

*Researched: 2026-04-06 16:24 CDT*

# Real-Time Subsurface Scattering (SIGGRAPH 2025 Advances)

## Key Finding
SIGGRAPH 2025 "Advances in Real-Time Rendering in Games" course includes a dedicated presentation on real-time subsurface scattering with reduced reliance on precomputed data.

## Highlights
- **Source**: SIGGRAPH 2025 Advances course (Vancouver) — PDF available at advances.realtimerendering.com
- **Trend**: Real-time SSS moving toward physically-based geometry interaction without heavy precomputation
- **Techniques**: Order-independent transparency combined with real-time SSS
- **Relevance to SOMA**: Critical for anatomical tissue rendering (skin, organs, fat layers) in the 3D viewer

## WebGPU Landscape (2026)
- WebGPU has universal browser support since late 2025
- Three.js adapting to WebGPU backend for large-scale scenes
- forge3d (Rust/wgpu) provides Python-accessible WebGPU renderer — potential alternative pipeline

## SOMA Integration Notes
- SSS shader skill (soma-sss-shaders) should reference SIGGRAPH 2025 techniques
- Consider compute-shader-based SSS for mobile (WKWebView now supports WebGPU on iOS 18+)
- The PDF course notes likely contain shader pseudocode adaptable to WGSL


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://github.com/milos-agathon/forge3d
