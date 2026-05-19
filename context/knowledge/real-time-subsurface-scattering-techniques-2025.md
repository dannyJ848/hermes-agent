# real-time-subsurface-scattering-techniques-2025

*Researched: 2026-04-06 20:22 CDT*

# Real-Time Subsurface Scattering Techniques for Anatomy Rendering

## Overview
Subsurface scattering (SSS) is critical for realistic anatomy visualization — skin, organs, and tissue all exhibit translucency where light enters and exits at different points.

## Key Concepts (from MJP/GPU Gems synthesis)

### When SSS Matters
- Standard diffuse BRDF (Lambertian) works when scattered light exits within the pixel footprint
- SSS becomes necessary when light diffuses beyond pixel boundaries (translucent materials)
- For anatomy: skin, ears, fingers, organ tissue all require SSS for realism

### Real-Time Approaches (ordered by quality/cost)

1. **Diffusion Profile Approximation** (GPU Gems 3 / d'Eon & Irving)
   - Sum of Gaussians to approximate diffusion profile
   - Screen-space blur using the profile as kernel weights
   - Most common in games; works well for skin
   - Cost: 1 extra fullscreen pass per profile

2. **Pre-Integrated Skin Shading** (Penner & Borshukov)
   - Pre-compute scattering into LUT textures
   - No blur passes needed — lookup based on curvature + N·L
   - Very fast; acceptable quality for mobile
   - **Best for SOMA mobile target**

3. **Separable Subsurface Scattering** (Jimenez et al.)
   - 2-pass separable blur in screen space
   - Uses diffusion profile kernel
   - Good quality/performance tradeoff
   - Standard in Unreal Engine

4. **Hybrid ReSTIR + Diffusion** (SIGGRAPH 2025 Advances)
   - Ray-traced paths for complex scattering + diffusion approximation
   - State of the art but requires RT cores
   - Not viable on mobile WebGPU yet

### SOMA Recommendation
For mobile WebGPU anatomy viewer:
- **Primary**: Pre-Integrated Skin Shading (LUT-based, no blur passes)
- **Fallback**: Simple wrap lighting with subsurface color tint
- **Future**: Separable SSS when WebGPU compute shaders mature on iOS

### Implementation Notes
- Diffusion profiles differ per tissue type (skin vs organ vs bone)
- For anatomy: use higher scattering radius than game skin (organs are more translucent)
- WebGL1 fallback: use rim-light fake with subsurface color
- WebGPU: can do proper screen-space SSS with compute shaders

## Sources
- MJP SSS Introduction: https://therealmjp.github.io/posts/sss-intro/
- GPU Gems 3 Ch.14: https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- SIGGRAPH 2025 Real-Time SSS: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf


## Sources

- https://therealmjp.github.io/posts/sss-intro/
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
