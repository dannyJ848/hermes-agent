# realtime-sss-webgpu-2025

*Researched: 2026-04-06 13:10 CDT*

# Real-Time Subsurface Scattering: State of the Art (2025)

## Key Sources
- **SIGGRAPH 2025 Advances Course**: Full dedicated session on real-time SSS, including hybrid ReSTIR-path tracing + diffusion approach. PDF published at advances.realtimerendering.com/s2025/.
- **NVIDIA RTX Skin (GDC 2025)**: First implementation of SSS in ray-traced gaming via RTX Remix. Part of RTX Kit neural rendering suite.
- **Neural Shading via DirectX 12**: Cooperative Vectors in Agility SDK Preview (April 2025) enables Tensor Core access from HLSL shaders. This is the pathway to neural SSS on desktop.
- **RTX Neural Texture Compression + Streaming**: Tile-based streaming that only decompresses accessed texture portions. Reduces memory for large anatomy models.

## Relevance to SOMA
1. **RTX Skin pattern**: The hybrid ReSTIR-path tracing + diffusion approach could inspire SOMA's SSS shader — even on mobile, a simplified diffusion approximation is viable.
2. **Neural shading**: Future-proofing — as WebGPU gains cooperative matrix operations, neural SSS becomes possible in-browser.
3. **Texture streaming**: Tile-based approach directly applicable to SOMA's high-res anatomy textures on mobile (reduce memory from 200MB+ textures).
4. **GitHub resource**: Jaysmito101/AdvancedVulkanDemos has open-source SSS implementation with reference markdown.

## Implementation Notes
- The SIGGRAPH 2025 hybrid approach uses ReSTIR for path sampling + diffusion profile for scattering. Mobile can use just the diffusion profile (no ReSTIR).
- NVIDIA's approach confirms separable Gaussian kernel SSS is still production-standard.
- For WebGPU: cooperative matrix ops not yet available, but compute-shader-based diffusion is feasible today.


## Sources

- https://advances.realtimerendering.com/s2025/
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos
