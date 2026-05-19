# reSTIR-subsurface-scattering-2024-2025

*Researched: 2026-04-06 19:23 CDT*

# ReSTIR Subsurface Scattering for Real-Time Path Tracing

**Source:** HPG 2024 (Kit) + SIGGRAPH 2025 Advances in Real-Time Rendering
**Authors:** Mirco Werner et al. (Karlsruhe Institute of Technology)
**GitHub:** https://github.com/MircoWerner/ReSTIR-SSS

## Core Innovation

A **hybrid ReSTIR-path tracing + diffusion** approach for real-time subsurface scattering that combines:

1. **ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)** applied to subsurface scattering paths
2. **Hybrid shift mapping** — reuses samples between pixels for noise reduction
3. **Sequential shift** — improves sample reuse across frames
4. **Diffusion approximation** for multiple-scattering (fast, physically-grounded)

## Key Results
- Significantly reduces noise and denoising artifacts in real-time rendering
- Path-traced SSS with limited bounces is cheaper than unknown bounce counts
- Diffusion evaluation remains very fast as a complement to path tracing
- Targets RT-capable GPUs (RTX-class hardware)

## SIGGRAPH 2025 Extension
The SIGGRAPH 2025 "Real-Time Subsurface Scattering" talk builds on this with:
- Hybrid ReSTIR-PT + diffusion theory refinement
- Better separation of single vs. multiple scattering contributions
- Practical implementation guidelines for game engines

## Relevance to SOMA

### Direct Applicability (HIGH)
SOMA renders anatomical tissue which critically depends on SSS for visual realism:
- **Skin rendering** — ears, fingers, nose need light transmission (wax-like glow)
- **Organ tissue** — liver, kidney, muscle all exhibit subsurface scattering
- **Blood vessels** — translucency through thin tissue layers

### Implementation Path for SOMA (WebGPU/Three.js)
Since SOMA targets mobile WebGPU:
1. **Screen-space SSS** remains the most practical approach (GPU Gems 3, Jimenez SSSS)
2. **Burley's normalized diffusion** (used in Disney BSDF) is the gold standard for offline → real-time
3. **12-tap Gaussian blur** approximation (Uncharted 2 / Shader X7) is proven for real-time
4. For WebGPU: separable SSS passes (horizontal + vertical Gaussian) at half-res, composited back

### Practical SOMA SSS Pipeline
```
1. Depth pre-pass
2. Opaque render
3. SSS pass (screen-space, separable blur with profile kernel)
4. Translucency pass (wrap lighting for thin features)
5. Composite
```

### Resource Links Collected
- Separable SSS (Jimenez): https://www.iryoku.com/separable-sss/
- Burley Disney BSDF: https://blog.selfshadow.com/publications/s2015-shading-course/burley/
- Efficient Screen-Space Burley Diffusion (Siggraph 2018): https://advances.realtimerendering.com/s2018/
- MJP SSS Introduction: https://therealmjp.github.io/posts/sss-intro/
- Real-Time Realistic Skin Translucency: https://www.iryoku.com/translucency/
- NVIDIA GPU Gems Ch14 (Skin): https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14

## Status
- Paper published HPG 2024, code available on GitHub
- SIGGRAPH 2025 talk extends with diffusion hybrid
- Open-source implementation available for study


## Sources

- https://dl.acm.org/doi/abs/10.1145/3675372
- https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
- https://github.com/MircoWerner/ReSTIR-SSS
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
