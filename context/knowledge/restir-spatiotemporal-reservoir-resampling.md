# ReSTIR-spatiotemporal-reservoir-resampling

*Researched: 2026-04-06 05:20 CDT*

# ReSTIR: Spatiotemporal Reservoir Resampling for Real-Time Ray Tracing

## Summary
ReSTIR (Bitterli et al., 2020, NVIDIA Research) enables real-time direct lighting from **millions of light sources** without complex acceleration structures. Critical for SOMA's anatomy viewer where scene complexity grows with tissue layers.

## Core Algorithm
1. **Resampled Importance Sampling (RIS):** Approximate the rendering integral by:
   - Choose a suboptimal but easy-to-sample source PDF (e.g., proportional to emitted radiance)
   - Generate M candidate samples from source PDF
   - Randomly select one sample weighted toward target PDF (p̂ ∝ ρ · Le · G)
   - Apply correction factor to get unbiased estimator

2. **Weighted Reservoir Sampling (WRS):** Single-pass algorithm to sample N elements from a stream without storing all candidates. Maintains a "reservoir" — a subset of seen elements, selecting/discarding based on relative weight.

3. **Spatiotemporal Reuse:** Key innovation — reuse samples across both:
   - **Spatial:** neighboring pixels in current frame
   - **Temporal:** same pixel across previous frames
   This dramatically reduces variance without more rays.

## SOMA Relevance
- **Anatomy scenes** have complex lighting: subsurface scattering, multi-layer tissue, cavity interiors
- Traditional path tracing too noisy with few samples; ReSTIR provides clean results with few samples
- Could enable realistic global illumination in the 3D viewer
- **WebGPU compatibility:** ReSTIR uses compute shaders — maps well to WebGPU compute pipeline
- Three.js WebGPU renderer is maturing; could integrate when targeting desktop

## Implementation Notes
- GitHub reference: `tatran5/Reservoir-Spatio-Temporal-Importance-Resampling-ReSTIR`
- Requires compute shader support (WebGPU, not WebGL2)
- World-space variant (AMD SA2021) improves screen-space artifacts
- Best combined with denoiser for final output

## Sources
- NVIDIA Research paper: https://research.nvidia.com/sites/default/files/pubs/2020-07_Spatiotemporal-reservoir-resampling/ReSTIR.pdf
- Tutorial: https://gamehacker1999.github.io/posts/restir/
- AMD World-Space variant: https://gpuopen.com/download/SA2021_WorldSpace_ReSTIR.pdf
- Reference implementation: https://github.com/tatran5/Reservoir-Spatio-Temporal-Importance-Resampling-ReSTIR


## Sources

- https://research.nvidia.com/sites/default/files/pubs/2020-07_Spatiotemporal-reservoir-resampling/ReSTIR.pdf
- https://gamehacker1999.github.io/posts/restir/
- https://gpuopen.com/download/SA2021_WorldSpace_ReSTIR.pdf
- https://github.com/tatran5/Reservoir-Spatio-Temporal-Importance-Resampling-ReSTIR
