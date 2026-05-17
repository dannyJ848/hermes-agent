# webgpu-realtime-path-tracing-2026

*Researched: 2026-04-06 18:28 CDT*

# WebGPU Real-Time Path Tracing (2026)

## Source
James Randall's blog — full real-time path tracer in WebGPU compute shaders, rendering Doom WAD levels in-browser. No ray-tracing cores, no ML denoisers.

## Key Technical Details
- **Pure compute shaders**: Entire path tracer runs in WebGPU compute (no rasterization pass)
- **BVH acceleration**: Bounding Volume Hierarchy for triangle intersection
- **Monte Carlo importance sampling**: Random ray sampling with the rendering equation (Kajiya 1986)
- **Temporal accumulation**: Accumulates samples across frames for convergence
- **Spatial denoising**: Post-process to reduce noise
- **60fps on Mac** at moderate resolution with defaults
- **Rendering equation**: Lo(x,ωo) = Le(x,ωo) + ∫Ω fr(x,ωi,ωo) · Li(x,ωi) · (ωi·n) dωi

## Relevance to SOMA
- WebGPU compute shaders can handle real-time path tracing — far simpler subsurface scattering is absolutely feasible
- BVH + compute shader pattern applies directly to anatomy mesh rendering
- Temporal accumulation could be used for SSS convergence on skin/tissue
- The approach needs no hardware RT cores — works on any WebGPU device

## SIGGRAPH 2025 SSS Reference
Found SIGGRAPH 2025 "Advances in Real-Time Rendering" course with dedicated SSS section:
- Hybrid ReSTIR path tracing + diffusion for real-time subsurface scattering
- PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf

## Action Items for SOMA
1. Extract the compute shader patterns from Randall's approach for WebGPU SSS
2. Study SIGGRAPH 2025 SSS paper for diffusion approximation techniques
3. Apply temporal accumulation to SOMA's native SSS shaders for convergence


## Sources

- https://www.jamesdrandall.com/posts/building-a-real-time-path-tracer-in-webgpu/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
