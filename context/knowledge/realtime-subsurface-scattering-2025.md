# realtime-subsurface-scattering-2025

*Researched: 2026-04-06 06:40 CDT*

# Real-Time Subsurface Scattering: 2025 State of the Art

## Key Developments

### 1. ReSTIR Subsurface Scattering (SIGGRAPH 2025 / HPG 2024)
- **Paper**: "ReSTIR Subsurface Scattering for Real-Time Path Tracing" (Zeng et al., Dec 2025)
- **Core innovation**: Applies ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) to subsurface scattering paths
- **Key insight**: Traditional screen-space SSS approximations fail with path tracing. ReSTIR-SSS enables real-time path-traced subsurface scattering by reusing light paths across space and time
- **Suitable for**: RTX/DXR hardware with hardware ray tracing (RT cores)

### 2. Hybrid ReSTIR-Path-Tracing + Diffusion (SIGGRAPH 2025 Advances)
- **Presentation**: "Real-Time Subsurface Scattering via Hybrid ReSTIR-Path-Tracing and Diffusion"
- **Approach**: Combines path tracing for direct/indirect SSS with diffusion-based approximation for multi-scatter
- **Advantage**: Handles indirect SSS with refraction — previous methods only handled direct illumination
- **Performance**: Real-time on modern RTX hardware

### 3. Classical Foundation: Gaussian Diffusion Profile (GPU Gems 3, d'Eon & Luebke)
- Sum of Gaussians approximation to the diffuse subsurface scattering profile
- 6-term Gaussian fit for skin:
  - R(0.0064, 0.2), R(0.0484, 0.2), R(0.187, 0.2), R(0.567, 0.2), R(1.99, 0.2), R(7.41, 0.2)
- Screen-space blur approach: render to texture, apply separable Gaussian blur with these weights
- **Still the best approach for non-RT hardware** (WebGPU without ray tracing)

## SOMA Application: Anatomy Viewer SSS

### Recommended Approach for WebGPU (no RT cores):
1. **Screen-space Gaussian diffusion** from GPU Gems 3 — proven, well-documented
2. **Pre-integrated skin shading** (Penner & Borshukov 2011) — even simpler, works on any GPU
3. **Wrap lighting + transmission** for translucent organs — cheap approximation

### Implementation Path for SOMA:
1. Use Three.js `MeshPhysicalMaterial` with `transmission` and `thickness` for organ translucency
2. Custom WGSL shader for screen-space SSS blur (if more realism needed)
3. Separate pre-pass for depth + normal → blur pass → combine with lighting
4. Tune diffusion profiles per tissue type (skin vs muscle vs organ)

### Tissue-Specific Diffusion Profiles:
- **Skin**: Standard 6-Gaussian profile (d'Eon)
- **Muscle**: Higher scattering, reddish absorption
- **Organs (liver, kidney)**: Very high scattering, moderate absorption
- **Fat/adipose**: Low scattering, yellowish transmission
- **Bone**: Almost no SSS, mostly specular + Lambertian

## Performance Budget (mobile WebGPU):
- Screen-space SSS blur: ~1-2ms at 1080p (separable 2-pass)
- Pre-integrated skin: ~0.1ms (just a texture lookup)
- Full path-traced SSS: NOT feasible on mobile (requires RT cores)


## Sources

- https://dl.acm.org/doi/abs/10.1145/3675372
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://www.youtube.com/watch?v=AtFBbMnUgoc
