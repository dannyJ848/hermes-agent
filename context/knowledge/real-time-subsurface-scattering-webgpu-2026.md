# real-time-subsurface-scattering-webgpu-2026

*Researched: 2026-04-06 12:46 CDT*

# Real-Time Subsurface Scattering for WebGPU Anatomy Rendering

## Key Techniques for SOMA Skin Rendering

### 1. Separable Subsurface Scattering (Jimenez et al.)
- **Paper**: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
- Separable 2D Gaussian blur approximation of BSSRDF diffusion profile
- Can be implemented as two 1D passes (horizontal + vertical) — **ideal for WebGPU compute shaders**
- Key insight: skin diffusion profile can be decomposed into sum of Gaussians with different weights/radii
- Performance: runs at 60fps even on mobile GPUs when using separable approach

### 2. Screen-Space Subsurface Scattering
- Post-process technique: render scene normally, then blur in screen space using skin diffusion kernel
- Requires a "skin mask" (material ID or SSS factor in G-buffer)
- Implementable in WebGPU with multi-render-target G-buffer pass + compute shader blur

### 3. Translucency Approximation (Barre-Brisebois GDC 2011)
- **Slides**: https://www.slideshare.net/slideshow/colin-barrebrisebois-gdc-2011-approximating-translucency-for-a-fast-cheap-and-convincing-subsurfacescattering-look-7170855/7170855
- Cheap wrapped diffuse lighting + view-dependent translucency term
- No precomputation needed — pure shader math
- Best for thin features: ears, nose, fingers
- **SOMA recommendation**: Use this as LOD fallback when full SSS is too expensive on mobile

### 4. SIGGRAPH 2025 Advances Course: Real-Time SSS
- **Paper**: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Latest state-of-the-art techniques presented at SIGGRAPH 2025
- Includes analytical Monte Carlo framework with variance reduction
- Claims "significantly more detail with much closer ground truth matching"

### 5. GPU Gems Resources
- **GPU Gems 3 Ch.14**: https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- **GPU Gems Ch.16**: https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- Texture-space vs screen-space approaches compared
- Detailed implementation walkthroughs

### Implementation Priority for SOMA
1. **Phase 1 (now)**: Wrapped diffuse + translucency approximation — zero cost, immediate visual improvement
2. **Phase 2**: Separable SSS via WebGPU compute shaders — medium cost, dramatic improvement
3. **Phase 3**: Analytical Monte Carlo from SIGGRAPH 2025 paper — high cost, reference quality

### Skin Texture Assets
- Free skin textures: https://github.com/Vulpinii/skin-texture/tree/master

### Reference Implementation
- Vulkan demos with SSS: https://github.com/Jaysmito101/AdvancedVulkanDemos


## Sources

- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
