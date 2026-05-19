# restir-subsurface-scattering-realtime

*Researched: 2026-04-06 19:27 CDT*

# ReSTIR Subsurface Scattering for Real-Time Path Tracing (HPG 2024)

**Authors:** Mirco Werner, Vincent Schüßler, Carsten Dachsbacher (KIT Karlsruhe)
**Published:** HPG 2024 (ACM)
**DOI:** 10.1145/3675372
**GitHub:** https://github.com/MircoWerner/ReSTIR-SSS (51 stars, MIT license)

## Key Innovation

Applies reservoir-based spatiotemporal importance resampling (ReSTIR) to subsurface light transport paths using BSSRDF importance sampling. This overcomes the noise limitations of path-traced diffusion approximation for subsurface scattering (SSS).

## Why This Matters for SOMA

- **Directly applicable:** SOMA's 3D anatomy viewer needs realistic skin/organ rendering with subsurface scattering
- **Real-time capable:** ReSTIR makes SSS practical at interactive frame rates
- **Open source:** MIT-licensed Vulkan implementation available at the GitHub repo
- **Better than screen-space:** Current screen-space SSS approximations (blur-based) have known artifacts — this path-traced approach eliminates them

## Technical Details

- Uses BSSRDF importance sampling for subsurface paths
- ReSTIR resampling leverages spatiotemporal coherence to reduce variance
- Implemented in Vulkan (VkRaven framework)
- Overcomes limitations of screen-space diffusion approximations

## SOMA Integration Path

1. Study the BSSRDF sampling approach from the paper
2. Adapt the ReSTIR resampling strategy for WebGPU (SOMA's target)
3. The native Three.js SSS approach (soma-sss-shaders skill) can be enhanced with ReSTIR-inspired importance sampling
4. Priority: Mobile WebGPU support is still limited — consider fallback to precomputed diffusion profiles

## Related: SIGGRAPH 2025 Advances

A SIGGRAPH 2025 talk ("Real-Time Subsurface Scattering" at Advances course) covers combining path tracing with real-time SSS — potential updated techniques beyond this paper.

## Sources
- ACM DL: https://dl.acm.org/doi/abs/10.1145/3675372
- PDF: https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
- Code: https://github.com/MircoWerner/ReSTIR-SSS

## Sources

- https://github.com/MircoWerner/ReSTIR-SSS
- https://dl.acm.org/doi/abs/10.1145/3675372
- https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
