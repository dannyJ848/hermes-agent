# threejs-webgpu-2026-sss-medical-rendering

*Researched: 2026-04-05 16:51 CDT*

# Three.js WebGPU in 2026: Implications for Medical 3D Anatomy Rendering

## Key Developments (as of March 2026)

### Three.js r171+ WebGPU Renderer (Sept 2025)
- Production-ready WebGPU renderer via `import { WebGPURenderer } from 'three/webgpu'`
- Zero-configuration setup with automatic WebGL fallback
- Three.js downloads hit 2.7M/week on NPM (270x nearest competitor)

### Performance Gains
- **100x performance improvement** for LiDAR point clouds and millions of particles
- Compute shaders now available for: collision detection, real-time filtering, simulation
- Reduced memory overhead with enhanced instancing for large models
- Segments.ai migrated LiDAR tool from WebGL→WebGPU (2025-2026) with major perf wins

### Subsurface Scattering (SSS) State
- Three.js discourse shows community demand for screen-space SSS (no built-in advanced SSS yet)
- Basic SSS example exists in three.js/examples but lacks medical-grade realism
- SIGGRAPH 2025 "Advances in Real-Time Subsurface Scattering" published (PDF) — covers multi-scatter volume rendering

### TSL (Three Shading Language)
- Simplifies shader development for WebGPU
- Makes custom SSS implementations more accessible without raw WGSL

## Relevance to SOMA
- **Models <500MB**: Three.js WebGPU is ideal — SOMA anatomy models typically fall in this range
- **SSS for skin/tissue**: Still requires custom shader work, but TSL makes it more approachable
- **Mobile**: WebGPU supported in Safari 18+ (iOS 18) — critical for SOMA's iOS target
- **Recommendation**: Plan migration from WebGLRenderer to WebGPURenderer once SOMA's base rendering is stable. Use TSL for custom tissue shaders.

## Sources
- altersquare.io (Three.js vs WebGPU 2026 comparison)
- Three.js discourse (SSS shader discussion)
- SIGGRAPH 2025 SSS course


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
