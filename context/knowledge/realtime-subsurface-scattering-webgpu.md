# realtime-subsurface-scattering-webgpu

*Researched: 2026-04-05 12:23 CDT*

# Real-Time Subsurface Scattering (SSS) for Anatomy Rendering

## Key Technique: Separable Subsurface Scattering (d'Eon & Luebke, NVIDIA GPU Gems 3 Ch.14)

### Core Concept
Skin translucency comes from light entering the surface, scattering through tissue, and exiting elsewhere. Without SSS, scanned skin models look "hard and dry" — unrealistic. SSS is THE critical differentiator for medical anatomy rendering.

### Two-Component Model
1. **Surface reflectance (~6% of light)**: Fresnel interaction with oily top layer. Use a specular BRDF (Kelemen/Szirmay-Kalos model preferred over Blinn-Phong for accuracy). NOT colored.
2. **Subsurface scattering (remaining ~94%)**: Light enters skin, scatters through epidermis/dermis/subcutaneous layers, partially absorbed by melanin/hemoglobin, exits at different point. THIS gives the soft, realistic look.

### Separable Approximation for Real-Time
The key insight: 2D diffusion convolution can be separated into two 1D passes (horizontal + vertical), making it O(n) instead of O(n²). This is the technique that makes real-time SSS feasible on GPU.

**Implementation pipeline for WebGPU:**
1. Render scene to G-buffer (albedo, normal, depth, thickness map)
2. Screen-space blur pass 1 (horizontal) with skin diffusion profile kernel
3. Screen-space blur pass 2 (vertical) with same kernel
4. Combine with specular pass

### Diffusion Profile
Skin has specific scattering radii per color channel (RGB scatter differently):
- Red scatters furthest (~2.4mm)
- Green medium (~1.4mm)  
- Blue least (~0.7mm)

Use Gaussian sum approximation: profile ≈ 0.233*G(0.0064) + 0.100*G(0.0484) + 0.118*G(0.187) + 0.113*G(0.567) + 0.358*G(1.99) + 0.078*G(7.24)

### Performance Target
Reddit reports <2-3ms for screen-space SSS using thickness maps. Fully viable for mobile at 30fps with optimization.

### Application to SOMA
For SOMA's 3D anatomy viewer, SSS would dramatically improve realism of:
- Muscular tissue (red subsurface glow)
- Organ surfaces (translucent membranes)
- Skin layers in cross-sections
- Blood vessel visibility through tissue

**Implementation priority**: Start with screen-space thickness-based approach (< 3ms cost) rather than full volumetric SSS. Thickness maps can be precomputed from anatomy meshes.

## Sources
- NVIDIA GPU Gems 3, Ch.14 (d'Eon & Luebke)
- Reddit r/GraphicsProgramming: thickness map + screen-space diffusion, <2-3ms
- ScienceDirect: illumination model decomposition for real-time SSS

## Sources

- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
- https://www.sciencedirect.com/science/article/pii/S1877705812001841
