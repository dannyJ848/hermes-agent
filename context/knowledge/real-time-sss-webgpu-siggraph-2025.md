# real-time-sss-webgpu-siggraph-2025

*Researched: 2026-04-05 12:40 CDT*

# Real-Time Subsurface Scattering for Medical 3D (2025-2026)

## SIGGRAPH 2025: Hybrid ReSTIR-Path Tracing + Diffusion for SSS
- **Source**: Advances in Real-Time Rendering in Games, SIGGRAPH 2025 (celebrating 20th anniversary)
- **Technique**: Hybrid approach combining ReSTIR (Reservoir-based Spatiotemporal Importance Resampling) path tracing with diffusion profiles for real-time subsurface scattering
- **Key insight**: Traditional screen-space SSS approximations are being replaced by hybrid methods that approach path-traced quality at real-time frame rates
- **Relevance to SOMA**: This hybrid approach could dramatically improve tissue realism in 3D anatomy viewer. Diffusion profiles (the classic approach) work well for skin but hybrid methods handle organs, muscle, and varied tissue densities better.
- **Paper**: ACM dl.acm.org/doi/abs/10.1145/3675372 — "ReSTIR Subsurface Scattering for Real-Time Path Tracing"
- **PDF**: advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

## GPU Gems Chapter 16: Classic SSS Approximations (Still Relevant)
- **Source**: NVIDIA GPU Gems, Chapter 16
- **Techniques covered**:
  1. **Wrap Lighting** — simplest approximation: `max(0, (dot(L,N) + wrap) / (1 + wrap))` softens diffuse boundary
  2. **Texture-based diffusion profile** — encode diffuse falloff + color shift (toward red for skin/blood) in a 1D texture
  3. **Color shift at shadow boundaries** — blood/tissue absorbs light, causing red shift where skin is thin (ears, nostrils)
- **For SOMA**: Wrap lighting + texture-based profile is the minimum viable SSS for anatomical models. Could implement in WGSL (WebGPU Shading Language) as a post-process blur.

## WebGPU for Medical AI (Feb 2026)
- **Paper**: "WebGPU Accelerated Client-Side AI for Privacy Preserving Dermatological Diagnostics" (Patel, 2026)
- **Key insight**: WebGPU enables client-side medical AI with privacy preservation via local differential privacy
- **Relevance**: Demonstrates WebGPU is production-ready for medical applications. Validates SOMA's WebGPU approach for anatomy rendering.

## Actionable for SOMA
1. **Immediate**: Implement wrap lighting in WGSL for tissue softening (1-line change)
2. **Short-term**: Add diffusion profile texture (1D LUT) for skin/tissue color shift
3. **Medium-term**: Evaluate ReSTIR-SSS hybrid once WebGPU ray tracing extensions mature
4. **Architecture**: Keep SSS as a composable shader module in the rendering pipeline


## Sources

- https://advances.realtimerendering.com/s2025/
- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://dl.acm.org/doi/abs/10.1145/3675372
- https://www.researchgate.net/publication/401110730
