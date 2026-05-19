# siggraph-2025-realtime-sss-neural-rendering

*Researched: 2026-04-06 03:49 CDT*

# SIGGRAPH 2025 & GDC 2025: Real-Time SSS and Neural Rendering Advances

## Key Finding: Hybrid ReSTIR Path Tracing + Diffusion for SSS (SIGGRAPH 2025)
- SIGGRAPH 2025 "Advances in Real-Time Rendering" course includes a major new SSS technique
- **Hybrid ReSTIR-Path Tracing + Diffusion**: Novel hybrid solution combining path tracing with diffusion approximation
- Paper available at: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Claims significantly more detail capture with much closer ground truth matching for skin rendering
- Presentation video: https://www.youtube.com/watch?v=AtFBbMnUgoc

## NVIDIA RTX Neural Shaders (GDC 2025, March 2025)
- **Neural shading support coming to DirectX 12** via Agility SDK Preview (April 2025)
- Enables small neural networks inside programmable shaders for improved IQ + performance
- Cooperative Vectors support in DirectX/HLSL enables Tensor Core access from shaders
- **RTX Skin**: One of first implementations of SSS in ray-traced gaming (via RTX Remix)
- Applications: textures, materials, lighting — broad relevance to anatomy rendering

## RTX Kit Technologies Relevant to SOMA
- **RTX Neural Texture Compression**: Tile-based decompression — only decompresses accessed texture portions
- **RTX Texture Streaming**: Divides textures into tiles, loads on demand — minimizes memory overhead
- **RTX Mega Geometry**: Path-tracing massive dense geometry (now in UE5 NvRTX branch)
- **DLSS 4**: 100+ games/apps supported, transformer model for dramatic IQ improvement

## Open-Source SSS Reference
- Reddit post with real-time SSS + translucency demo
- Code: https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
- Practical Vulkan-based implementation with reference shader code

## SOMA Application Notes
- For WebGPU-based anatomy viewer, the diffusion approximation approach is most practical
- Neural texture compression pattern could inform LOD strategy for medical textures
- RTX Skin's SSS approach validates that real-time subsurface scattering is achievable at interactive framerates
- The hybrid ReSTIR+Diffusion approach could inspire a simplified WebGPU shader for skin/organ translucency
- Open-source Vulkan SSS reference from Jaysmito101 is directly adaptable to WGSL shaders


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
- https://github.com/Jaysmito101/AdvancedVulkanDemos
