# siggraph-2025-sss-webgpu-advances

*Researched: 2026-04-05 23:58 CDT*

# SIGGRAPH 2025 & WebGPU Advances for Medical Rendering

## SIGGRAPH 2025 Real-Time SSS Course
- **Source**: SIGGRAPH 2025 Advances in Real-Time Rendering course
- **URL**: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- **Key Innovation**: Hybrid ReSTIR-Path Tracing & Diffusion for real-time subsurface scattering
- **Relevance to SOMA**: Directly applicable to 3D anatomy rendering — realistic skin/tissue visualization requires accurate SSS
- **Technique**: Combines path tracing (ReSTIR) with diffusion approximation for real-time performance
- **Video**: https://www.youtube.com/watch?v=AtFBbMnUgoc

## WebGPU Ecosystem (Feb 2025)
- Three.js now has WebGPU renderer with significantly improved performance
- MLS-MPM fluid simulations running on WebGPU at high particle counts
- Virtual pipes method for real-time shallow water physics
- AI models (TTS, multimodal) running entirely in-browser via WebGPU
- DeepSeek's Janus Pro: multimodal AI running locally in browser
- **Implication**: WebGPU is mature enough for production medical visualization

## Reddit SSS Resources
- https://github.com/Jaysmito101/AdvancedVulkanDemos — Vulkan SSS demos adaptable to WebGPU
- Active community working on real-time SSS translucency

## SOMA Integration Notes
- The hybrid ReSTIR + diffusion approach could be adapted for WebGPU compute shaders
- Three.js WebGPU renderer now production-ready — validates SOMA's Three.js stack choice
- MLS-MPM techniques could simulate tissue deformation in anatomy viewer
- Consider targeting WebGPU compute for SSS rather than screen-space post-processing


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://www.webgpuexperts.com/best-webgpu-updates-february-2025
- https://github.com/Jaysmito101/AdvancedVulkanDemos
