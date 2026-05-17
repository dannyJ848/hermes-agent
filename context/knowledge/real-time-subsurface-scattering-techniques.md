# real-time-subsurface-scattering-techniques

*Researched: 2026-04-06 20:02 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering

## Overview
Subsurface scattering (SSS) is critical for realistic skin/organic tissue rendering. Standard diffuse BRDFs (Lambertian) assume scattered light exits within the same pixel footprint — adequate for opaque materials but wrong for translucent tissue (skin, organs, muscles).

## Key Concepts

### When SSS Matters
- SSS becomes visible when scattered light exits *outside* the original pixel footprint
- For skin/tissue: light diffuses through the medium, absorbing certain wavelengths
- This creates characteristic "glow" at thin edges (ears, fingers, organ membranes)

### Real-Time Approximation Approaches (from MJP's survey + NVIDIA GPU Gems Ch.16)

1. **Screen-Space Diffusion** (most common in games)
   - Render diffuse lighting to texture
   - Apply Gaussian blur kernels (multiple passes at different radii)
   - Blend based on scattering radius per material
   - Works well but fails at geometric silhouettes

2. **Pre-Integrated Skin Shading** (Penner & Borsodi 2011)
   - Pre-compute scattering lookup textures
   - No blurring passes needed — single shader evaluation
   - Best for mobile/WebGPU where bandwidth is limited
   - **RECOMMENDED for SOMA** — minimal GPU overhead

3. **Transmission/Translucency Approximation**
   - Wrap lighting: `NdotL = dot(N, L) * 0.5 + 0.5` (half-lambert)
   - Add view-dependent translucency for thin features
   - Cheap, works in any shader pipeline

4. **SIGGRAPH 2025 Advances** (from PDF find)
   - Latest techniques achieve near-ground-truth skin rendering
   - Improved diffusion profiles matching measured skin data
   - Significant detail capture improvement over previous methods

### SOMA Implementation Strategy
- **Tier 1 (mobile-safe):** Half-Lambert wrap lighting + translucency falloff for all tissue
- **Tier 2 (WebGPU):** Pre-integrated skin shading with lookup textures
- **Tier 3 (desktop):** Screen-space diffusion with multi-pass Gaussian blur
- All tiers: Red/warm subsurface color tint for biological tissue realism

## Sources
- NVIDIA GPU Gems Ch.16: Real-Time Approximations to SSS
- MJP Blog: Introduction to Real-Time SSS
- SIGGRAPH 2025 Advances in Real-Time Rendering (SSS session)
- Jaysmito101 AdvancedVulkanDemos SSS reference


## Sources

- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://therealmjp.github.io/posts/sss-intro/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
