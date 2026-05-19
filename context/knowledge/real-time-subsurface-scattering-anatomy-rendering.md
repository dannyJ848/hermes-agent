# real-time-subsurface-scattering-anatomy-rendering

*Researched: 2026-04-06 03:39 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering

## Overview
Subsurface scattering (SSS) is critical for realistic anatomy visualization — skin, tissue, and organs all exhibit translucency where light enters, scatters internally, and exits at a different point. This is especially important for thin anatomical structures (ears, nostrils, fingers) where the effect is most visible.

## Key Techniques (Complexity: Low → High)

### 1. Wrap Lighting (Simplest — Oren-Nayar approximation)
```glsl
float diffuse = max(0, dot(L, N));
float wrap_diffuse = max(0, (dot(L, N) + wrap) / (1 + wrap));
```
- `wrap` parameter (0-1) controls how far light wraps around the surface
- Reduces contrast, softens lighting — cheap approximation
- Can encode in a texture indexed by `dot(L, N)` for GPU efficiency
- Add color shift toward red at low values to simulate blood scattering

### 2. Texture-Based Approach
- Encode wrap lighting + color shift in a 1D/2D lookup texture
- Include specular power function in alpha channel
- Extremely efficient on mobile/WebGPU — single texture fetch

### 3. Gaussian Diffusion Profile
- Model SSS as sum of Gaussians with different weights and variances
- For skin: typically 6 Gaussians fitted to measured BSSRDF data
- Render in screen space using multiple blurred passes at different kernels
- SIGGRAPH 2025 advances: ReSTIR path tracing + diffusion hybrid for real-time

### 4. Screen-Space SSS (Jimenez et al.)
- Separable blur in screen space using diffusion kernel
- Two-pass (horizontal + vertical) — very GPU-friendly
- Used in Unreal Engine, Unity HDRP

## WebGPU Implementation Notes for SOMA
- WebGPU supports compute shaders → can do screen-space blur efficiently
- Texture-based wrap lighting works immediately in fragment shaders
- For mobile iOS: stick to wrap lighting + texture LUT for performance
- Reserve multi-pass Gaussian blur for desktop/high-end devices
- SIGGRAPH 2025 hybrid ReSTIR approach requires ray tracing — not yet in WebGPU

## Anatomical Relevance
- **Skin**: Most visible SSS effect. Red color shift from blood scattering.
- **Ears/Nostrils**: Thin tissue shows strong translucency
- **Organs**: Soft, wet surfaces — moderate SSS needed
- **Bone/Teeth**: Minimal SSS but slight translucency at thin edges
- **Blood vessels**: Deep red scattering visible through thin skin

## Sources
- NVIDIA GPU Gems Chapter 16: Real-Time Approximations to Subsurface Scattering
- SIGGRAPH 2025 Advances: Real-Time SSS via Hybrid ReSTIR-Path Tracing & Diffusion
- Jaysmito101 Vulkan SSS demos (GitHub)
- WebGPU Gaussian Splatting (Visionary) — neural rendering approach


## Sources

- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
