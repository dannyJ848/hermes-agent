# real-time-subsurface-scattering-restir-siggraph2025

*Researched: 2026-04-06 03:56 CDT*

# Real-Time Subsurface Scattering via Hybrid ReSTIR-Path Tracing & Diffusion

**Source:** SIGGRAPH 2025, Advances in Real-Time Rendering in Games (20th Anniversary)
**Author:** Tanki Zhang (NVIDIA)
**Also:** KIT/ACM paper "ReSTIR Subsurface Scattering for Real-Time Path Tracing" (DOI: 10.1145/3675372)

## Technique Overview

A novel hybrid approach combining **volumetric path tracing with ReSTIR** (Reservoir-based Spatiotemporal Importance Resampling) and **diffusion profile approximation** for real-time subsurface scattering.

### Key Innovation
- Traditional real-time SSS relies on screen-space diffusion approximations (e.g., separated Gaussian profiles, screen-space blur) — these miss volumetric light transport details
- Path-traced SSS is physically accurate but extremely noisy at real-time sample counts
- This hybrid method: uses ReSTIR to resample SSS paths spatiotemporally, combining **hybrid shift** and **sequential shift** strategies to dramatically reduce noise
- Falls back to diffusion profiles where path tracing is too expensive (thin geometry, backlit surfaces)

### ReSTIR for SSS
The paper applies ReSTIR's reservoir sampling to subsurface scattering paths:
- **Hybrid shift mapping**: Combines replay and random replay shift strategies for SSS path reuse
- **Sequential shift**: Reuses paths from previous frames with temporal coherence
- Result: Significantly reduced noise and denoising artifacts compared to brute-force path tracing
- Works in the context of real-time path tracing pipelines (RTX, DXR)

### Diffusion Profile Integration
- Uses physically-based diffusion profiles as a complementary/feedback signal
- When path samples are insufficient (e.g., few rays reach subsurface events), diffusion provides a smooth fallback
- The combination yields both sharp subsurface detail (from path tracing) and smooth overall appearance (from diffusion)

## Relevance to SOMA (3D Anatomy Viewer)

### Direct Application Potential
1. **Skin rendering**: Human skin is the #1 SSS material — ear backscattering, finger translucency, nose subsurface glow
2. **Organ visualization**: Soft tissue organs (liver, kidneys, brain) all exhibit SSS — realistic rendering requires it
3. **Mobile feasibility challenge**: ReSTIR requires RT cores — NOT available on mobile GPUs (SOMA's target platform)
4. **Adaptation strategy for WebGPU**:
   - Can implement diffusion-based SSS (Gaussian separation) in WebGPU compute shaders
   - The paper's diffusion profiles can be precomputed per tissue type
   - Path tracing portion requires desktop RT — could be a progressive enhancement for desktop WebGPU with ray queries
   - For mobile: screen-space Gaussian separation (2-pass blur) with tissue-specific scattering parameters remains the practical approach

### Practical Takeaway for SOMA
The **diffusion profile approach** validated by NVIDIA's research confirms that Gaussian separation SSS is production-quality when tuned correctly. For SOMA's mobile target:
- Pre-compute tissue-specific scattering parameters (mean free path, absorption coefficients)
- Use the separated Gaussian kernel approach (Jimenez/Separator SSS)
- Apply via WebGPU compute shaders in screen space
- Reserve path-traced SSS as a future desktop enhancement when WebGPU ray queries mature

### Key Parameters from Literature
- Skin scattering: ~2-4mm mean free path (red channel scatters deeper)
- Organ tissue: varies 1-10mm depending on density
- Blood-rich tissue: stronger red scattering, weaker blue/green absorption

## Sources
- SIGGRAPH 2025 Advances Course: https://advances.realtimerendering.com/s2025/
- ACM Paper: https://dl.acm.org/doi/abs/10.1145/3675372
- KIT PDF: https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
- YouTube Talk: https://www.youtube.com/watch?v=AtFBbMnUgoc


## Sources

- https://advances.realtimerendering.com/s2025/index.html
- https://dl.acm.org/doi/abs/10.1145/3675372
- https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
- https://www.youtube.com/watch?v=AtFBbMnUgoc
