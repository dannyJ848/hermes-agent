# realtime-subsurface-scattering-medical-3d-2025

*Researched: 2026-04-06 00:37 CDT*

# Real-Time Subsurface Scattering for Medical 3D Anatomy

## SIGGRAPH 2025 Advances Course (August 2025)
- Celebrates 20th anniversary of the Advances in Real-Time Rendering program
- Features a dedicated **Real-Time Subsurface Scattering** talk with published paper
- Hybrid ReSTIR-Path Tracing & Diffusion approach for SSS — combines path tracing with diffusion approximation
- Speakers from Activision, Ubisoft, Epic Games, id Software, NVIDIA, HypeHype
- Topics: SSS, real-time path tracing, order-independent transparency, strand-based hair/fur, stochastic direct lighting for many-lights (including mobile GPUs)

## Key SSS Techniques (from NVIDIA GPU Gems Ch.16)

### 1. Wrap Lighting (Simplest)
```glsl
float wrap_diffuse = max(0, (dot(L, N) + wrap) / (1 + wrap));
```
- `wrap` value 0-1 controls how far light wraps around surfaces
- Can encode in a 1D texture lookup indexed by `dot(L,N)`
- Add color shift toward red at low values to simulate blood scattering (skin)

### 2. Texture-Based Diffusion
- Simulate light bleeding by blurring the irradiance map
- Use multiple blur passes at different scales (kernel sizes)
- Weighted by distance from surface — farther = more attenuation/diffusion

### 3. Screen-Space Approaches
- Post-process blur in screen space to simulate SSS
- Lower cost than texture-space, but less physically accurate
- Good for mobile/low-end targets

## Relevance to SOMA
- **Anatomy rendering requires convincing skin/tissue translucency** — SSS is critical for organs, muscles, skin
- WebGPU supports compute shaders → can implement screen-space SSS efficiently
- The SIGGRAPH 2025 hybrid ReSTIR approach may be too expensive for mobile, but wrap lighting + texture encoding is very cheap
- **Recommended approach for SOMA**: Start with wrap lighting + 1D texture with red shift for skin, graduate to screen-space blur for organs
- The "many lights on mobile" talk from HypeHype is directly relevant to SOMA's mobile performance constraints

## Action Items for SOMA
1. Implement wrap lighting shader with configurable `wrap` parameter
2. Create 1D LUT texture with red-shift for skin tissue types
3. Profile screen-space SSS blur on iOS Safari WebGPU
4. Monitor SIGGRAPH 2025 proceedings (Aug 2025) for published ReSTIR-SSS paper


## Sources

- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://advances.realtimerendering.com/s2025/index.html
- https://www.youtube.com/watch?v=AtFBbMnUgoc
