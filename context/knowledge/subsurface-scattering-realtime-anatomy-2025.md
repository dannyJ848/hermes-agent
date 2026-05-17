# subsurface-scattering-realtime-anatomy-2025

*Researched: 2026-04-05 20:25 CDT*

# Subsurface Scattering for Real-Time 3D Anatomy Rendering

## SIGGRAPH 2025 Advances in Real-Time SSS
- NVIDIA unveiled a **hybrid real-time subsurface scattering technique** combining volumetric path tracing with a new physically-based model (SIGGRAPH 2025 "Advances in Real-Time Rendering" course, celebrating 20 years)
- Course covers innovations in SSS and real-time path tracing
- Source: https://advances.realtimerendering.com/s2025/

## GPU Gems 3 — Skin Rendering Foundation (d'Eon & Luebke, NVIDIA)
Key techniques applicable to anatomy rendering:

### Two-Component Reflectance Model
1. **Surface reflectance** (~6% of light): Fresnel interaction with oily topmost skin layer. Use physically-based specular BRDF (NOT Blinn-Phong). Kelemen/Szirmay-Kalos model recommended.
2. **Subsurface scattering**: Light enters tissue, scatters through multiple layers, exits in a 3D neighborhood. Gives skin its soft, translucent appearance.

### Multilayer Skin Model
- Minimum 2 layers below specular surface for realism (Donner & Jensen 2005)
- Single-layer model is insufficient — three-layer model produces significantly better results
- Medically, epidermis alone has 5 distinct layers (stratum corneum, lucidum, granulosum, spinosum, basale)
- For SOMA: 2-3 scattering layers is the sweet spot (performance vs realism)

### Key Insight for SOMA
- Even with high-detail normal/diffuse/specular maps from Z-Anatomy data, rendering looks "hard and dry" WITHOUT subsurface scattering
- SSS is THE differentiator between plastic-looking anatomy and realistic tissue
- For organs: different scattering parameters (liver, heart muscle, brain tissue all have distinct SSS profiles)
- For skin: ears and thin tissue show significant translucency (light passes through)

## WebGPU Implementation Considerations
- SSS via screen-space blur (Gaussian sum approximation of diffusion profile) is most practical for real-time
- Texture-space diffusion: render to UV-space texture, apply separable blur, composite back
- For mobile: profile must be separable (2 passes vs full 2D convolution) to hit frame budget
- Scattering radius varies by tissue type — configurable parameter per anatomical structure

## SOMA Integration Path
1. Start with **screen-space SSS** (simplest, good enough for mobile)
2. Use separable Gaussian kernels approximating diffusion profiles
3. Per-organ scattering parameters (stored in mesh metadata)
4. Future: WebGPU compute shaders for volumetric SSS on high-end devices

## Sources
- SIGGRAPH 2025 Advances in Real-Time Rendering: https://advances.realtimerendering.com/s2025/
- GPU Gems 3 Ch.14: https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- NVIDIA hybrid SSS (2025): https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/


## Sources

- https://advances.realtimerendering.com/s2025/
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
