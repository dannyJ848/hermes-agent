# subsurface-scattering-realtime-techniques-2025

*Researched: 2026-04-06 00:28 CDT*

# Real-Time Subsurface Scattering (SSS) for Anatomy Rendering

## SIGGRAPH 2025 Breakthrough: Hybrid ReSTIR-Path Tracing + Diffusion

NVIDIA unveiled a **hybrid real-time SSS technique** (SIGGRAPH 2025 Advances in Real-Time Rendering) that combines:
- **Volumetric path tracing** via ReSTIR (Reservoir-based Spatiotemporal Importance Resampling)
- **Diffusion approximation** for faster convergence
- Approaches path-traced quality at real-time frame rates

This is the most significant SSS advancement since the original screen-space diffusion approximations.

## Classic Foundation: GPU Gems 3 Chapter 14 (d'Eon & Luebke, NVIDIA)

Key principles for real-time skin rendering (directly applicable to SOMA's 3D anatomy viewer):

### 1. Two-Component Model
- **Surface reflectance** (~6% of light): Fresnel interaction with oily top layer. Requires physically-based specular BRDF (NOT Blinn-Phong). Use Kelemen/Szirmay-Kalos model or GGX.
- **Subsurface scattering** (~94% of light): Light enters skin, scatters through tissue layers, exits at different point. Gives skin its soft, translucent appearance.

### 2. Multi-Layer Skin Model
Skin is NOT a single scattering layer. Minimum viable model:
- **Epidermis** (outer layer): Thin, absorbs strongly in blue wavelengths
- **Dermis** (middle): Contains blood vessels — red scattering dominant
- **Subcutaneous** (deep): Fatty tissue, high scattering, yellow-ish

Single-layer models produce incorrect results. 2-3 layers minimum for convincing anatomy.

### 3. Diffusion Profile Approach
Instead of simulating individual photon paths, use **diffusion profiles**:
- Pre-compute Gaussian kernels approximating scattering per layer
- Apply as screen-space blur passes (texture-space or screen-space)
- d'Eon's dual Gaussian: `R(r) = 1.0 * exp(-|r|²/2v₁) + 0.3 * exp(-|r|²/2v₂)`
  - Where v₁, v₂ are variance parameters per skin layer

### 4. Practical Implementation for WebGPU/Three.js
For SOMA's mobile anatomy viewer:
1. **Screen-space SSS** (fastest): 3-pass Gaussian blur in screen space with depth-aware sampling
2. **Texture-space SSS**: Render to UV-space texture, apply diffusion, composite
3. **Pre-integrated SSS** (mobile-friendly): Use pre-computed lookup textures based on NdotL and curvature
4. **WebGPU compute SSS** (future): Use compute shaders for diffusion approximation

### 5. Mobile-Optimized Approach
For iOS WKWebView (SOMA's target):
- **Pre-integrated SSS** (Penner & Borshukov 2011) is most efficient
- Single texture lookup replacing multi-pass blur
- Works with forward rendering (no G-buffer needed)
- Quality: 80% of full diffusion at 10% of the cost

## SOMA Integration Path
1. Start with pre-integrated SSS for mobile compatibility
2. Use GGX specular for surface reflectance
3. Add WebGPU compute-based diffusion when WebGPU adoption matures
4. Long-term: implement hybrid ReSTIR approach for desktop/high-end

## Sources
- NVIDIA GPU Gems 3, Chapter 14 (d'Eon & Luebke)
- SIGGRAPH 2025: "Real-Time Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion"
- ACM DL: 10.1145/3721241.3744991


## Sources

- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://dl.acm.org/doi/10.1145/3721241.3744991
