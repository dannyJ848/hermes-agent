# realtime-sss-siggraph-2025

*Researched: 2026-04-06 19:34 CDT*

# Real-Time Subsurface Scattering Advances (SIGGRAPH 2025, GDC 2025)

## Key Developments

### 1. Hybrid ReSTIR-Path Tracing + Diffusion (SIGGRAPH 2025 Advances Course)
- Novel hybrid approach combining ReSTIR path tracing with diffusion-based SSS
- Presented at SIGGRAPH 2025 Advances in Real-Time Rendering course
- Source: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Significantly better skin detail matching vs ground truth with real-time performance

### 2. NVIDIA RTX Skin (GDC 2025, via RTX Remix)
- One of first implementations of SSS in ray-traced gaming
- Light transmits and scatters through skin realistically
- Part of NVIDIA RTX Kit neural rendering suite
- Requires RTX hardware (Tensor Cores)

### 3. Neural Shading in DirectX 12 (April 2025 Preview)
- Cooperative Vectors support added to DirectX/HLSL
- Enables accessing RTX Tensor Cores from within shaders
- Neural networks embedded in programmable shaders for SSS, materials, lighting
- Microsoft + NVIDIA collaboration

### 4. RTX Texture Streaming SDK
- Tile-based texture streaming reduces memory overhead
- Only decompresses/caches accessed texture portions
- Critical for medical 3D anatomy apps with large texture datasets

## SOMA Relevance
- ReSTIR hybrid approach could inspire WebGPU SSS shader implementation
- Neural shading in DX12 shows industry direction — WebGPU may follow
- RTX Skin validates real-time SSS in production games (anatomy apps next)
- Tile-based texture streaming pattern applicable to anatomy model LOD systems


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
