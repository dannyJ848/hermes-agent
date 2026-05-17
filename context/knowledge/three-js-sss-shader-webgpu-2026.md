# three-js-sss-shader-webgpu-2026

*Researched: 2026-04-06 01:46 CDT*

# Three.js SSS Shader + WebGPU Renderer for Anatomy (2026)

## Key Findings

### 1. Built-in SubsurfaceScatteringShader (Three.js Addon)
- Import: `import { SubsurfaceScatteringShader } from 'three/addons/shaders/SubsurfaceScatteringShader.js'`
- Based on GDC 2011 — "Approximating Translucency for a Fast, Cheap and Convincing Subsurface Scattering Look"
- It's a ShaderMaterial, not a full material — needs wrapping
- Limitation: Screen-space approach, not physically-based multi-layer SSS

### 2. Three.js WebGPU Renderer (r171+, Sept 2025)
- Production-ready as of r171: `import { WebGPURenderer } from 'three/webgpu'`
- Zero-configuration, automatic WebGL fallback
- Three.js downloaded 2.7M/week on NPM by March 2026 — 270x nearest competitor
- TSL (Three Shading Language) simplifies custom shader development

### 3. Performance Gains (WebGPU vs WebGL)
- 100x performance for LiDAR point clouds and millions of particles
- Compute shaders for collision detection, real-time filtering
- Reduced memory overhead, enhanced instancing for large models
- Segments.ai migrated LiDAR tool from WebGL→WebGPU: massive improvement

### 4. SOMA Integration Implications
- **Near-term**: Use built-in SubsurfaceScatteringShader for skin/organ translucency
- **Medium-term**: Migrate to WebGPURenderer (r171+) for compute shader benefits
- **TSL**: Custom anatomy shaders (muscle sheen, bone specular, fat translucency) become easier
- **Mobile concern**: WebGPU not yet universal on mobile Safari (WKWebView). Need WebGL fallback.
- **Recommendation**: Start with WebGL SSS shader, plan WebGPU migration path for when iOS Safari supports it

### Sources
- Three.js SSS Shader docs: https://threejs.org/docs/pages/module-SubsurfaceScatteringShader.html
- Three.js vs WebGPU 2026: https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- Screen-space SSS discussion: https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939


## Sources

- https://threejs.org/docs/pages/module-SubsurfaceScatteringShader.html
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939
