# webgpu-sss-advances-2025

*Researched: 2026-04-06 04:37 CDT*

# WebGPU & Subsurface Scattering Advances (2025)

## SIGGRAPH 2025 — Real-Time SSS Course
- **Source**: "Real-Time Subsurface Scattering" course at SIGGRAPH 2025 Advances in Real-Time Rendering
- **Key technique**: Hybrid ReSTIR-Path Tracing + Diffusion for RT subsurface scattering
- **PDF**: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- **Video**: https://www.youtube.com/watch?v=AtFBbMnUgoc
- **Relevance to SOMA**: ReSTIR-based SSS could be adapted for WebGPU compute shaders for realistic skin/tissue rendering in anatomy viewer

## WebGPU Ecosystem (Feb 2025)
- **Three.js WebGPU renderer** now production-ready (used in Expo 2025 fluid simulation)
- **MLS-MPM fluid simulation** running smoothly on WebGPU (Matsuoka_601)
- **Kokoro TTS** — WebGPU-accelerated browser TTS (local, no cloud)
- **SmolVLM** — multimodal AI running entirely in browser via WebGPU
- **Key insight**: Three.js WebGPU renderer is mature enough for production installations

## Practical SSS Implementation
- **GitHub resource**: https://github.com/Jaysmito101/AdvancedVulkanDemos (subsurface_scattering.md)
- Vulkan-based but concepts translate to WebGPU compute shaders
- **Virtual pipes method** for fluid physics (lisyarus) — applicable to blood flow visualization

## SOMA Integration Notes
1. Three.js WebGPU renderer can replace WebGL for SSS shaders
2. ReSTIR-PT + diffusion hybrid is state-of-the-art for real-time SSS
3. Compute shader approach avoids fullscreen pass overhead of traditional SSS
4. MLS-MPM technique could simulate tissue deformation for interactive dissection


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.webgpuexperts.com/best-webgpu-updates-february-2025
- https://github.com/Jaysmito101/AdvancedVulkanDemos
