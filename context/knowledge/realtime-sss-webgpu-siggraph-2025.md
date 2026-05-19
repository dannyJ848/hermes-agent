# realtime-sss-webgpu-siggraph-2025

*Researched: 2026-04-06 05:37 CDT*

# Real-Time Subsurface Scattering: SIGGRAPH 2025 & GDC 2025 Advances

## Key Sources

### SIGGRAPH 2025 — Advances in Real-Time Rendering Course
- **Dedicated SSS session**: "Real-Time Subsurface Scattering" — a full course at SIGGRAPH 2025 Advances
- **Hybrid ReSTIR-Path Tracing + Diffusion**: Novel hybrid approach combining path tracing with diffusion-based SSS for real-time performance
- Presenters demonstrated significantly more detailed skin rendering with closer ground truth matching
- Course materials: `advances.realtimerendering.com/s2025/`

### NVIDIA GDC 2025 — RTX Neural Shaders & RTX Skin
- **RTX Skin**: One of the first implementations of sub-surface scattering in ray-traced gaming (via RTX Remix)
- **RTX Neural Shaders**: Small neural networks embedded in programmable shaders for improved IQ and performance
- **DirectX 12 support**: Neural shading via Agility SDK Preview (April 2025), enabling Tensor Core access from HLSL shaders
- **Cooperative Vectors**: New DirectX/HLSL feature enabling matrix-vector ops critical for neural rendering inference inside shaders
- **RTX Texture Streaming SDK**: Tile-based texture streaming that pairs with Neural Texture Compression — relevant for medical atlas textures

### Community Implementation (Jaysmito101)
- Open-source Vulkan subsurface scattering demo with detailed markdown explanation
- Code: `github.com/Jaysmito101/AdvancedVulkanDemos`
- Demonstrates real-time translucency + SSS combination

## Relevance to SOMA
1. **RTX Neural Shader approach** could inspire WebGPU compute shader implementations of SSS for anatomy skin rendering
2. **Cooperative Vectors in DX12** — watch for WebGPU equivalent (subgroup operations)
3. **Tile-based texture streaming** directly applicable to high-res medical texture atlases
4. **Hybrid path-tracing + diffusion** — could simplify SOMA's SSS pipeline from multi-pass to single-pass

## Action Items for SOMA
- Monitor WebGPU spec for cooperative vector / tensor core access features
- Consider neural-network-based SSS approximation in compute shaders for mobile fallback
- Study Jaysmito101's Vulkan SSS demo for portable techniques


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos
