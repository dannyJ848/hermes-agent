# tsl-webgpu-field-guide

*Researched: 2026-04-02 17:55 CDT*

# TSL (Three Shading Language) + WebGPU Field Guide

**Source:** blog.maximeheckel.com (Oct 2025) -- comprehensive guide
**Relevance:** Essential for converting SOMA's GLSL SSS shaders to TSL

## Key Concepts

### TSL vs GLSL vs WGSL
- **TSL** = Three.js Shading Language, a JS-based functional shading language
- Compiles to both **GLSL** (WebGL) and **WGSL** (WebGPU) automatically
- Replaces `onBeforeCompile` GLSL injection with NodeMaterial system
- TSL shaders are renderer-agnostic -- write once, run on both backends

### NodeMaterial System
- Replace `MeshPhysicalMaterial + onBeforeCompile` with `MeshPhysicalNodeMaterial`
- Custom shader logic via `.colorNode`, `.normalNode`, `.emissiveNode`, etc.
- No more string-based GLSL injection

### R3F WebGPU Integration
- Use `extend(THREE_WEBGPU)` to register WebGPU elements
- Async `gl` prop on Canvas for WebGPURenderer
- Classic Three.js materials work but need `extend` for node materials
- Known issue: R3F's extend function may need workarounds for node materials

### Compute Shaders
- Available in WebGPU via `computeNode`
- Use cases: particles, instanced mesh animation, physics, post-processing
- Directly applicable to SOMA: heartbeat simulation, blood flow

### Conversion Pattern
```js
// Old: GLSL injection
material.onBeforeCompile = (shader) => {
  shader.fragmentShader = shader.fragmentShader.replace(
    '#include <color_fragment>',
    customGLSL
  );
};

// New: TSL node material
const material = new MeshPhysicalNodeMaterial();
material.colorNode = mix(baseColor, sssColor, blendFactor);
```

## Action Items for SOMA
1. Convert SubsurfaceScattering.ts from GLSL injection to TSL nodes
2. Use `MeshPhysicalNodeMaterial` for all anatomy materials
3. Keep LUT generation (renderer-agnostic, no changes needed)
4. Test compute shaders for heartbeat animation


## Sources

- https://blog.maximeheckel.com/posts/field-guide-to-tsl-and-webgpu/
