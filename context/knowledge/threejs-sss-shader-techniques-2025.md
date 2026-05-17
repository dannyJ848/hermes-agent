# threejs-sss-shader-techniques-2025

*Researched: 2026-04-05 22:43 CDT*

# Three.js SSS Shader Techniques (2025 Research)

## Screen-Space Subsurface Scattering for Skin Rendering

### Key Reference: Der Schmale (David Lenaerts)
- David Lenaerts ("Der Schmale") is the primary reference for screen-space SSS in Three.js
- His technique implements screen-space subsurface scattering for realistic skin rendering
- Referenced by Three.js community as the gold standard for real-time SSS
- Website: derschmale.com

### Three.js SSS Approaches
1. **Built-in SSS**: Three.js examples include a basic SSS shader (examples/jsm/shaders/SubsurfaceScatteringShader)
2. **Screen-Space SSS** (advanced): Works in screen-space using deferred rendering, much more realistic for skin/organic tissue
3. **PBR-based SSS**: Custom shader approaches using physically-based scattering approximations

### WebGPU Migration Impact (2026)
- Three.js r171+ supports zero-config WebGPU renderer
- Custom GLSL shaders need TSL (Three Shading Language) conversion for WebGPU
- Post-processing pipelines need WebGPU-compatible alternatives
- Compute shaders available in WebGPU enable more advanced SSS techniques

### Relevance to SOMA
- **Anatomy rendering**: SSS is critical for realistic tissue appearance (skin, muscle, organs)
- **Mobile considerations**: Screen-space SSS is GPU-intensive; may need LOD fallback for mobile
- **Three.js example shader**: Good starting point for SOMA's tissue rendering pipeline
- **TSL migration**: Plan shader development in TSL for future WebGPU compatibility

### Sources
- Three.js forum thread: discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939
- Der Schmale SSS article: derschmale.com
- Three.js WebGPU migration: utsubo.com/blog/webgpu-threejs-migration-guide


## Sources

- https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939
- https://www.utsubo.com/blog/webgpu-threejs-migration-guide
- https://derschmale.com
