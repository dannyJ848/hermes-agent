# webgpu-sss-realtime-2025

*Researched: 2026-04-06 13:55 CDT*

# WebGPU Real-Time Subsurface Scattering (2025)

## SIGGRAPH 2025 SSS Course
- Dedicated course: "Real-Time Subsurface Scattering" at SIGGRAPH 2025 Advances in Real-Time Rendering
- PDF: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- YouTube: https://www.youtube.com/watch?v=AtFBbMnUgoc
- **Key technique**: Hybrid ReSTIR-Path Tracing + Diffusion for real-time SSS
- This is the state-of-the-art for real-time subsurface scattering in games/rendering

## WebGPU Ecosystem (Feb 2025)
- Three.js now has a WebGPU renderer with significant performance improvements
- MLS-MPM fluid simulations running smoothly on consumer hardware in browser
- Material Point Method (MPM) outperforming SPH for high particle counts
- WebGPU enabling large-scale interactive installations (Expo 2025)

## SOMA Relevance
- Three.js WebGPU renderer could enable better SSS for anatomy without custom shader overhead
- The ReSTIR-Path Tracing approach may be adaptable for medical tissue rendering
- MPM techniques could be used for soft tissue deformation simulation
- Key code reference: https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md

## Action Items for SOMA
1. Monitor Three.js WebGPU renderer maturity for SSS shader support
2. Study the SIGGRAPH 2025 PDF for diffusion approximation techniques portable to WebGPU
3. Evaluate if ReSTIR sampling can work within mobile GPU constraints


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.webgpuexperts.com/best-webgpu-updates-february-2025
- https://www.youtube.com/watch?v=AtFBbMnUgoc
