# siggraph-2025-realtime-sss-webgpu

*Researched: 2026-04-05 15:58 CDT*

# SIGGRAPH 2025: Real-Time Subsurface Scattering Advances

## Key Finding
SIGGRAPH 2025 "Advances in Real-Time Rendering" course published a dedicated SSS session (PDF available at advances.realtimerendering.com/s2025/).

### Hybrid ReSTIR-Path Tracing + Diffusion
- Novel hybrid approach combining ReSTIR path tracing with diffusion approximation for real-time SSS
- Replaces legacy separable SSS (Jimenez et al.) with screen-space RT-based approach
- Relevant to SOMA: Could replace our custom SSS shader with a more physically accurate approach

### WebGPU Ecosystem Status (Feb 2025)
- Three.js WebGPU renderer now production-ready (used in Expo 2025 installations)
- MLS-MPM fluid simulations running on WebGPU at high particle counts
- Kokoro TTS running in-browser via WebGPU compute shaders
- Consumer hardware capable of real-time physics at scale

### SOMA Implications
1. **SSS Upgrade Path**: SIGGRAPH 2025 hybrid ReSTIR + diffusion approach could replace our pre-integrated SSS with a more accurate real-time method
2. **Three.js WebGPU Renderer**: Now viable for SOMA — could unlock compute shaders for medical volume rendering
3. **Mobile Feasibility**: MLS-MPM simulations run smoothly on older devices — suggests WebGPU anatomy rendering is feasible on mobile

### Sources
- SIGGRAPH 2025 Advances Course: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- ReSTIR SSS Talk: https://www.youtube.com/watch?v=AtFBbMnUgoc
- WebGPU Feb 2025 Roundup: https://www.webgpuexperts.com/best-webgpu-updates-february-2025
- Open-source SSS reference: https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md

## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.webgpuexperts.com/best-webgpu-updates-february-2025
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
