# three.js-webgpu-sss-2026

*Researched: 2026-04-05 23:05 CDT*

# Three.js WebGPU SSS & Performance — 2026 State

## Key Findings

### Three.js WebGPU SSS Example
- Three.js now has a built-in **fast subsurface scattering** material example for WebGPU: `webgpu_materials_sss.html`
- Falls back to WebGL2 backend when WebGPU unavailable
- Author credit: Shaochun Lin
- **SOMA relevance:** This is a drop-in reference for implementing tissue translucency in the anatomy viewer

### Three.js WebGPU Renderer (r171+, Sept 2025)
- Production-ready WebGPURenderer with zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- Auto-fallback to WebGL2 when WebGPU not available (critical for iOS Safari)
- Three.js downloaded **2.7M times/week** on NPM by March 2026 — 270x nearest competitor
- TSL (Three Shading Language) simplifies custom shader development

### Performance Gains (WebGPU vs WebGL)
- **100x performance** gains for LiDAR point clouds and millions of particles
- Compute shaders for collision detection, real-time filtering
- Reduced memory overhead, enhanced instancing for large models
- Segments.ai: transitioned LiDAR tool from WebGL→WebGPU between 2025-2026, significant speedup

### Practical Decision for SOMA
- **Three.js WebGPU** is the right choice (models <500MB, rapid development)
- Native WebGPU only needed for models >500MB or complex simulations
- TSL shader development is simpler than raw WGSL
- WebGPU universal browser support since late 2025

### SIGGRAPH 2025 SSS Paper
- Available at: `advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf`
- Covers volume scattering after surface transmission with multiple internal bounces
- **Action item:** Extract techniques for tissue-specific SSS profiles (skin vs organ vs bone)

## SOMA Integration Path
1. Use Three.js r171+ WebGPURenderer with WebGL2 fallback
2. Reference `webgpu_materials_sss` example for tissue translucency
3. Define tissue-specific SSS profiles (skin=subsurface red, liver=deep red, bone=white opaque)
4. Leverage TSL for custom medical shader effects
5. Test performance on mobile Safari with WebGL2 fallback


## Sources

- https://threejs.org/examples/webgpu_materials_sss.html
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
