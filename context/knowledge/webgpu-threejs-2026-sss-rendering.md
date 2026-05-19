# webgpu-threejs-2026-sss-rendering

*Researched: 2026-04-05 19:28 CDT*

# WebGPU + Three.js for Real-Time SSS Rendering (2026 State)

## Key Findings

### Three.js WebGPU Renderer (r171+, Sept 2025)
- Production-ready `WebGPURenderer` with zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- WebGL fallback for unsupported browsers
- Three.js downloaded 2.7M/week on NPM by March 2026 (270x nearest competitor)
- Three Shading Language (TSL) simplifies shader development vs raw WGSL

### Performance Gains
- **100x performance improvement** for LiDAR point clouds and millions of particles
- Compute shaders available for: collision detection, real-time filtering, SSS precomputation
- Reduced memory overhead via enhanced instancing for large models
- Segments.ai case study: migrated from WebGL to WebGPU 2025-2026, massive LiDAR perf gains

### SIGGRAPH 2025 Real-Time SSS
- Dedicated SIGGRAPH 2025 course: "Advances in Real-Time Rendering" includes real-time subsurface scattering
- Focus: less reliance on precomputation, physically-based geometry interaction
- Order-independent transparency techniques advancing alongside SSS

### SOMA Architecture Implications
1. **Immediate**: Three.js r171+ WebGPU path enables compute shader SSS without leaving Three.js ecosystem
2. **TSL shaders**: Can write SSS compute shaders in TSL (simpler than raw WGSL)
3. **Mobile**: WebGPU supported in Safari 18+ (iOS 18+), covering modern iPhones
4. **Fallback path**: WebGL SSS (current approach) remains as fallback for older devices
5. **Memory**: Enhanced instancing means more anatomy models loaded simultaneously
6. **Recommendation**: Plan migration to WebGPURenderer for SOMA v2, keeping WebGL as fallback

### When to Use Native WebGPU vs Three.js WebGPU
- Three.js WebGPU: models <500MB, rapid prototyping, simpler shader needs
- Native WebGPU: models >500MB, custom compute pipelines, specialized simulations
- For SOMA anatomy models (<100MB typically), Three.js WebGPU is the right choice

## Sources
- Altersquare article on Three.js vs WebGPU 2026
- SIGGRAPH 2025 Advances in Real-Time Rendering course
- Three.js r171 release notes


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.reddit.com/r/GraphicsProgramming/comments/1mnmgy5/siggraph_2025_vancouver_megathread/
