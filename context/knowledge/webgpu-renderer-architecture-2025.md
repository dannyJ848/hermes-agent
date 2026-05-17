# webgpu-renderer-architecture-2025

*Researched: 2026-04-06 16:03 CDT*

# WebGPU Renderer Architecture (2025)

## Source: Ryosuke's Blog (Sep 2025)
URL: https://whoisryosuke.com/blog/2025/structure-of-a-webgpu-renderer/

## Key Insights for SOMA

### WebGPU vs OpenGL/WebGL Differences
- WebGPU uses an **immutable stateless system** — must be explicit about setup, memory management, GPU procedures
- OpenGL's global state functions (glCreateShader, glUseProgram) don't exist in WebGPU
- Architecture patterns from OpenGL tutorials don't transfer directly

### Renderer Architecture Pattern
- Scene-based: provide any scene with models, materials, lights
- API similar to Three.js / Babylon.js
- Shader management is fundamentally different — no global state
- Compute shaders available for audio visualization + 3D mixing

### Relevance to SOMA
- SOMA uses Three.js currently (via WKWebView on iOS)
- Migration path: Three.js → WebGPU native could improve performance
- Compute shaders could enable real-time tissue simulation (SSS, deformation)
- State management approach more suitable for complex anatomy scenes with many objects

## SIGGRAPH 2025: Real-Time Subsurface Scattering
- Paper from SIGGRAPH 2025 "Advances in Real-Time Rendering" course
- Covers SSS via hybrid ReSTIR path tracing + diffusion approximation
- PDF available at: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Key technique: volume scattering after surface transmission with multiple internal bounces
- Could be adapted for WebGPU compute shaders in anatomy rendering


## Sources

- https://whoisryosuke.com/blog/2025/structure-of-a-webgpu-renderer/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
