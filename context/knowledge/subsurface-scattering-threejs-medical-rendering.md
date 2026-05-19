# subsurface-scattering-threejs-medical-rendering

*Researched: 2026-04-05 17:34 CDT*

# Subsurface Scattering for Real-Time Medical Anatomy Rendering (Three.js/WebGL)

## Date: 2026-04-05

## Summary
Research into practical SSS implementations for Three.js-based medical anatomy viewers (SOMA project). Covers built-in MeshPhysicalMaterial support, community shaders, SIGGRAPH 2025 advances, and architecture approaches.

## Key Findings

### 1. Three.js Built-in SSS Support (MeshPhysicalMaterial)
Three.js `MeshPhysicalMaterial` has native SSS-capable properties:
- **`thickness`**: Thickness of the volume beneath the surface (world space units). Controls how far light travels inside.
- **`attenuationColor`**: Color that white light turns into due to absorption. Default (1,1,1).
- **`attenuationDistance`**: Average distance light travels before interacting with a particle (world space). Must be >0. Default Infinity.
- **`transmission`**: Enables physically-based transparency (light passes through vs reflects).
- **`ior`**: Index of refraction (1.0-2.333). Skin ≈ 1.4, fat ≈ 1.44.

**SOMA Application:** Set `thickness` per-vertex or via texture for organ models. Use `attenuationColor` matching tissue absorption spectra (red blood = red attenuation). `attenuationDistance` varies by tissue density.

### 2. Community: MeshTranslucentMaterial by N8Programs
- Dedicated SSS material for Three.js: `@n8programs/mesh-translucent-material`
- Demo: https://threejs-subsurface.vercel.app/
- More specialized than MeshPhysicalMaterial, likely better for skin/organ rendering
- YouTube demo available

### 3. SIGGRAPH 2025 Advances Course
- Title: "Real-Time Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion"
- Introduces hybrid approach combining path tracing (ReSTIR) with diffusion approximation
- Probably too heavy for mobile/WebGL but concepts applicable to WebGPU future

### 4. SSS Fundamentals (from MJP's Introduction)
- **Problem:** Translucent materials (skin, organs, fat) scatter light beyond pixel footprint
- **Screen-space approach:** Render irradiance to texture → Gaussian blur in screen space → combine with surface rendering
- **Diffusion profile:** Characterizes how light spreads through material. Key profiles: dipole, multipole, normalized diffusion
- **Separable vs non-separable:** 2D Gaussian blur can be split into horizontal + vertical passes for performance
- **Texture-space vs screen-space:** Texture-space blurs in UV space (consistent regardless of distance), screen-space blurs in pixel space (simpler but has edge artifacts)

### 5. Three.js Anatomy Ecosystem
- Z-Anatomy provides free Blender models exportable to GLB for Three.js
- Forum discussion confirms feasibility of layer-based anatomy visualization
- Multiple community members building similar systems with Three.js + WebGL

## SOMA Implementation Recommendation
For mobile (iOS WKWebView + Three.js):
1. **Phase 1 (now):** Use `MeshPhysicalMaterial` with `thickness` + `attenuationColor` + `attenuationDistance` for basic SSS
2. **Phase 2:** Explore `MeshTranslucentMaterial` for higher quality on organs
3. **Phase 3 (WebGPU):** Implement screen-space diffusion blur for skin rendering when WebGPU is widely available on iOS

## Performance Notes
- MeshPhysicalMaterial SSS properties have higher per-pixel cost than MeshStandardMaterial
- On mobile, limit SSS-enabled meshes to primary dissected organs, not full body
- Consider LOD: disable SSS at distance, enable on close-up dissection view

## Sources
- https://threejs.org/docs/pages/MeshPhysicalMaterial.html
- https://therealmjp.github.io/posts/sss-intro/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813
- https://www.youtube.com/watch?v=Mp_R8JS8_MM (MeshTranslucentMaterial demo)


## Sources

- https://threejs.org/docs/pages/MeshPhysicalMaterial.html
- https://therealmjp.github.io/posts/sss-intro/
- https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813
- https://www.youtube.com/watch?v=Mp_R8JS8_MM
