# threejs-webgpu-2026-construction-large-models

*Researched: 2026-04-06 00:59 CDT*

# Three.js vs WebGPU 2026: Implications for SOMA 3D Anatomy Viewer

## Key Findings (Source: Altersquare, March 2026)

### Three.js r171+ WebGPU Renderer (Production-Ready)
- Released September 2025 with zero-config import: `import { WebGPURenderer } from 'three/webgpu'`
- 2.7M weekly NPM downloads by March 2026 (270× nearest competitor)
- WebGL fallback maintained for backward compatibility
- TSL (Three Shading Language) simplifies shader development

### Performance Gains
- **100× improvement** on LiDAR point clouds and millions of particles
- Segments.ai case study: migrated LiDAR point cloud tool WebGL→WebGPU, massive perf gains
- Compute shaders now available for: collision detection, real-time filtering, custom effects
- Reduced memory overhead + enhanced instancing for large models

### Decision Framework for SOMA
| Feature | Three.js WebGPU | Native WebGPU |
|---------|----------------|---------------|
| Ease of Use | High | Low |
| Models <500MB | ✅ Ideal | Overkill |
| Compute Shaders | Via TSL | Full control |
| SSS / Custom Shaders | TSL abstracts | Raw WGSL |

### SOMA Implications
1. **Migration path**: Import WebGPURenderer from 'three/webgpu' — minimal code changes
2. **SSS shaders**: Use TSL for subsurface scattering instead of raw WGSL — faster dev
3. **Anatomy models**: Most anatomy meshes are well under 500MB — Three.js WebGPU is the sweet spot
4. **Point clouds**: If SOMA adds volumetric rendering (DICOM slices), compute shaders enable real-time processing
5. **Mobile Safari**: WebGPU support landed in Safari 18+ (late 2025) — critical for iOS SOMA app

### Action Items
- Update SOMA to Three.js r171+ and test WebGPURenderer with anatomy models
- Prototype SSS shader using TSL instead of custom WGSL
- Benchmark anatomy mesh rendering: WebGL vs WebGPU on mobile Safari


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
