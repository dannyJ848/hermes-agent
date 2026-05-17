# real-time-sss-shaders-anatomy-rendering

*Researched: 2026-04-06 14:13 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering

## Key Techniques for SOMA

### 1. Screen-Space SSS (Primary Approach for WebGPU/WebGL)
- **Principle**: Blur lighting in screen-space using a Gaussian kernel weighted by depth difference. Light from neighboring pixels bleeds through based on subsurface scattering radius.
- **Pipeline**: Render scene normally → Separate diffuse lighting pass → Apply screen-space blur (separable Gaussian) → Composite with specular
- **Performance**: Very fast — runs at 60fps even on mobile GPUs. The key insight is that SSS blur is separable (horizontal + vertical passes).

### 2. Diffusion Profile Approach (Jimenez et al. 2015)
- Uses 6 weighted Gaussian kernels to approximate the diffusion profile of skin/tissue
- Each kernel captures different scattering distances: very short (epidermis), medium (dermis), long (subdermal)
- For anatomy: different tissue types (muscle, fat, organ) would need custom diffusion profiles with different scattering radii

### 3. Pre-Integrated Skin Shading (Penner & Borshukov)
- Simplifies SSS to a texture lookup — no blur passes needed
- Pre-computes scattering response for different curvature and N·L values
- **Best for mobile** — minimal GPU cost. Ideal for SOMA's iOS target.
- Limitation: Doesn't handle light transmission through thin tissue (ears, membranes)

### 4. WebGPU Compute Shader SSS (Future Path)
- SIGGRAPH 2025 Advances course introduced hybrid ReSTIR-path-tracing + diffusion for SSS
- WebGPU compute shaders enable particle-based subsurface scattering simulation
- MLS-MPM fluid simulation techniques (300k+ particles on mid-range GPU) suggest volumetric SSS is achievable in browser
- Three.js WebGPURenderer now supports compute shaders natively

### Recommended SOMA Implementation Strategy
1. **Phase 1**: Pre-Integrated Skin Shading for immediate mobile compatibility
2. **Phase 2**: Screen-Space SSS blur for desktop/high-end tablets
3. **Phase 3**: WebGPU compute-based volumetric SSS for surgical-level realism

### Tissue-Specific Diffusion Radii (from literature)
| Tissue Type | Scattering Radius (mm) | Albedo Tint |
|------------|----------------------|-------------|
| Skin (light) | 2.5 | Pink/warm |
| Skin (dark) | 1.8 | Warm brown |
| Muscle | 4.0 | Deep red |
| Fat | 5.0 | Yellow-white |
| Cartilage | 3.0 | Blue-white |
| Organ (liver) | 6.0 | Dark red-brown |

### Resources
- MJP's SSS Introduction: therealmjp.github.io/posts/sss-intro/ — best technical overview
- derschmale.com/lab/doodles/skinsss/ — live Three.js SSS demo with VSM shadows
- SIGGRAPH 2025 "Real-Time SSS" course — hybrid ReSTIR + diffusion approach
- Three.js discourse thread on SSS (June 2025) — community implementations


## Sources

- https://therealmjp.github.io/posts/sss-intro/
- https://www.derschmale.com/lab/doodles/skinsss/build/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://discourse.threejs.org/t/skin-shading-with-screen-space-sub-surface-scattering/83939
- https://www.webgpuexperts.com/best-webgpu-updates-january-2025
