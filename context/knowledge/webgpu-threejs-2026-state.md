# webgpu-threejs-2026-state

*Researched: 2026-04-06 13:28 CDT*

# WebGPU + Three.js State (March 2026)

## Key Findings

### Three.js r171+ Production WebGPU (Sept 2025)
- `WebGPURenderer` is production-ready with zero-config: `import { WebGPURenderer } from 'three/webgpu'`
- WebGL fallback automatic
- Three.js downloads: 2.7M/week on NPM (270x nearest competitor)
- TSL (Three Shading Language) simplifies shader development

### Performance Benchmarks
- 100x performance gains on LiDAR point clouds and millions of particles
- Segments.ai migrated LiDAR point cloud labeling from WebGL→WebGPU: massive performance improvement
- Compute shaders enable: collision detection, real-time filtering on GPU
- Reduced memory overhead, enhanced instancing for large models

### When to Use What
| Approach | Best For | Limit |
|----------|----------|-------|
| Three.js WebGPU | Models <500MB, prototyping | Moderate perf for huge datasets |
| Native WebGPU | Models >500MB, simulations | Requires deep expertise |

### SIGGRAPH 2025: Real-Time SSS
- New hybrid ReSTIR-Path Tracing + Diffusion approach for real-time subsurface scattering
- Course: "Advances in Real-Time Rendering in Games" SIGGRAPH 2025
- Relevant to SOMA: anatomical rendering with skin/organ translucency
- Resource: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

## SOMA Implications
1. Three.js r171+ WebGPU renderer is now viable for SOMA's anatomy viewer
2. SSS for organ/skin translucency can use SIGGRAPH 2025 techniques adapted for WebGPU compute shaders
3. TSL shader language simplifies custom anatomy shader development
4. Mobile: WKWebView supports WebGPU as of Safari 18+ (iOS 18)


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
