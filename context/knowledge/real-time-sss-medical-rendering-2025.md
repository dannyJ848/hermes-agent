# real-time-sss-medical-rendering-2025

*Researched: 2026-04-05 23:16 CDT*

# Real-Time Subsurface Scattering for Medical Visualization (2025)

## SIGGRAPH 2025 Advances
- **Course**: "Advances in Real-Time Subsurface Scattering" (SIGGRAPH 2025)
- **Key innovation**: Hybrid ReSTIR-Path Tracing + Diffusion approach for real-time SSS
- **PDF**: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- This combines Monte Carlo path tracing with analytical diffusion models for real-time performance

## Technique Taxonomy for SOMA Anatomy Viewer

### Tier 1: Texture-based (fastest, WebGL compatible)
- **Separable SSS** (Jimenez et al.): Blur in screen-space, 2 passes. ~1ms cost.
- **Approximating Translucency** (Barre-Brisebois GDC 2011): Cheap wrap lighting + thickness map
- GPU Gems Ch.16: Thickness-based wrap lighting with color shift
- **Best for**: Mobile/WebGL fallback path in SOMA

### Tier 2: BSSRDF-based (balanced, WebGPU required)
- Dipole/Multipole diffusion: Physically-based, needs profile textures
- Pre-integrated skin shading: Epic's approach from Unreal, works with deferred
- **Best for**: Desktop/WebGPU primary path in SOMA

### Tier 3: Path-traced (highest quality, requires RT cores)
- ReSTIR-PT + Diffusion hybrid (SIGGRAPH 2025): Real-time path tracing of subsurface
- **Best for**: Future enhancement when WebGPU ray-tracing is available

## SOMA Integration Recommendations
1. **Immediate**: Implement texture-based SSS (Separable SSS or wrap lighting) for WebGL fallback
2. **Phase 2**: BSSRDF with pre-integrated profiles for WebGPU path
3. **Phase 3**: Hybrid ReSTIR when WebGPU RT becomes available in Safari/Chrome

## Key Resources
- Separable SSS paper: https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
- GPU Gems Ch.16: https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- AdvancedVulkanDemos SSS reference: https://github.com/Jaysmito101/AdvancedVulkanDemos
- Skin textures: https://github.com/Vulpinii/skin-texture


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- https://www.iryoku.com/separable-sss/downloads/Separable-Subsurface-Scattering.pdf
