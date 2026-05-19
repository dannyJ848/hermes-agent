# reSTIR-subsurface-scattering-realtime-2024

*Researched: 2026-04-06 13:16 CDT*

# ReSTIR Subsurface Scattering for Real-Time Path Tracing (HPG 2024)

**Authors:** Mirco Werner, Vincent Schüssler, Carsten Dachsbacher (KIT)
**Published:** HPG 2024 (Proc. ACM Comput. Graph. Interact. Tech., Vol 7, No 3, Article 36)
**DOI:** 10.1145/3675372
**Code available:** Yes (linked from author page)

## Problem
Screen-space SSS approximations are limited. Path tracing with diffusion approximation overcomes these limits but introduces high noise. Existing ReSTIR methods don't handle translucent subsurface transport well.

## Key Innovation
Applies **reservoir-based spatio-temporal importance resampling (ReSTIR)** to subsurface light transport paths specifically:

1. **BSSRDF importance sampling** for candidate generation
2. **Hybrid shift mapping** — observes that different image regions benefit from either:
   - **Reconnection shift** (reconnecting through translucent object)
   - **Delayed reconnection shift** (one vertex later)
   - Local SSS criterion deterministically selects the better shift
3. **Novel sequential shift** — instead of choosing one shift per path, runs sequential resampling passes with different shifts. The best shift is picked *implicitly* by resampling, avoiding the limitations of deterministic local choice.

## Results
- Real-time performance
- Significantly reduces noise vs standard path tracing at equal render time
- Reduces denoising artifacts in SSS-heavy regions
- Outperforms standard path tracing especially with increasing mean free paths

## Relevance to SOMA
SOMA's 3D anatomy viewer needs realistic skin/tissue rendering on mobile WebGPU. Current approach uses screen-space diffusion profiles (SSS- shaders skill). ReSTIR SSS could provide:
- Better quality at similar performance (path-traced SSS vs screen-space)
- Physically accurate tissue translucency (important for anatomical correctness)
- Noise reduction without heavy denoising passes (mobile-friendly)

**Caveat:** This is desktop GPU research. Mobile WebGPU adoption would require careful optimization — possibly using a simplified variant with fewer resampling passes.

## SIGGRAPH 2025 Update
NVIDIA is unveiling a **hybrid real-time SSS technique combining volumetric path tracing with new physically-based methods** at SIGGRAPH 2025 Advances in Real-Time Rendering course. This suggests ReSTIR SSS concepts are being productionized by major vendors.


## Sources

- https://mircowerner.com/posts/restir-sss/
- https://cg.ivd.kit.edu/publications/2024/restir-sss/restir-sss.pdf
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
