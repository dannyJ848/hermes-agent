# webgpu-medical-3d-2026

*Researched: 2026-04-04 20:10 CDT*

# WebGPU for Medical 3D: 2026 State

**Source:** Wishtree Technologies (March 2026)

## Key Data Points
- WebGPU has **~70% browser support** across major desktop browsers by 2026
- **2-3x performance improvement** over WebGL for GPU-heavy workloads
- **Compute shaders** enable simulations, large data processing, and AI inference on GPU
- Enables **zero-install** enterprise applications (digital twins, 3D configurators, training simulations)
- Medical imaging, automotive virtual showrooms, and real estate are key verticals

## SOMA Architecture Implications
- **SSS shaders**: Compute shaders in WebGPU would make subsurface scattering much faster — could precompute scattering tables on GPU
- **Mobile concern**: WebGPU on Safari iOS is still limited. Need WebGL fallback for iOS users
- **Triangle budgets**: 2-3x improvement means we could render more anatomical detail without frame drops
- **Zero-install advantage**: SOMA as a PWA with WebGPU acceleration competes with native apps like Complete Anatomy
- **On-device AI inference**: WebGPU compute shaders could run medical term NLP models locally — privacy-preserving

## Technical Migration Path
- Three.js supports WebGPU renderer (experimental since r158, more stable in r170+)
- SOMA should implement **WebGPU first, WebGL fallback** strategy
- Test with `navigator.gpu` detection before WebGPU path


## Sources

- https://wishtreetech.com/blogs/digital-product-engineering/unlocking-the-power-of-webgl-and-webgpu-the-zero-install-enterprise/
