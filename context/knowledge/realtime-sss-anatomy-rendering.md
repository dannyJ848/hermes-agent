# realtime-sss-anatomy-rendering

*Researched: 2026-04-06 14:34 CDT*

# Real-Time Subsurface Scattering for Anatomy Rendering

## State of the Art (SIGGRAPH 2025)

NVIDIA unveiled a **hybrid real-time SSS technique** combining volumetric path tracing with a new physically-based diffusion model at SIGGRAPH 2025 "Advances in Real-Time Rendering" (20th anniversary session).

Key paper: **"ReSTIR Subsurface Scattering for Real-Time Path Tracing"** (ACM TOG 2024)
- Combines ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) with subsurface scattering
- Moves beyond screen-space diffusion approximations
- Hybrid approach: path tracing for near-surface detail + diffusion for deep scattering

## Classical Foundation (GPU Gems 3, Ch. 14 — d'Eon & Luebke)

### Skin Rendering Pipeline
1. **Surface reflectance (~6% of light):** Fresnel interaction with oily topmost layer. Use a rough specular BRDF (NOT Blinn-Phong). Kelemen/Szirmay-Kalos model recommended.
2. **Subsurface scattering (remaining ~94%):** Light enters skin, scatters through layers (epidermis → dermis → subcutaneous), exits elsewhere. This gives skin its soft, translucent appearance.

### Critical Insight for SOMA
Without SSS, even highly detailed anatomy models look "hard, dry, and unrealistic." SSS is **absolutely vital** for realistic tissue rendering — this applies equally to anatomy education as to character rendering.

### Diffusion Profile Approach (d'Eon)
- Sum of Gaussians approximation to the diffusion profile
- Can be implemented as screen-space blur passes
- 6 Gaussian kernels capture the multi-layer scattering behavior
- Works in real-time on modern GPUs

## Implementation Paths for SOMA

### Path 1: Screen-Space Diffusion (Fastest, Good Quality)
- Render diffuse lighting to texture
- Apply Gaussian blur passes at different scales (sum of Gaussians)
- Weights tuned for skin/tissue scattering coefficients
- Works in WebGL2 with multiple render targets

### Path 2: Pre-Integrated Skin Shading (Mobile-Friendly)
- Jimenez et al. 2010 technique
- Pre-compute scattering into 2D LUT (curve × NdotL)
- Single texture lookup per pixel
- Best option for SOMA's mobile target (iOS/Mac)

### Path 3: WebGPU Compute Shaders (Future)
- When SOMA targets WebGPU
- Can implement full ReSTIR-SSS pipeline
- Hybrid path tracing + diffusion
- Would be state-of-the-art

## Scattering Coefficients for Tissue Types
Different tissue layers have different scattering profiles:
- **Epidermis:** Short-range scattering, slight reddish tint
- **Dermis:** Medium-range, more blood absorption (red)
- **Subcutaneous fat:** Long-range scattering, yellowish
- **Muscle tissue:** Different profile entirely (darker, more absorption)

For anatomy education, each tissue type needs its own scattering profile — this is a content authoring concern, not just a shader concern.


## Sources

- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://dl.acm.org/doi/abs/10.1145/3675372
