# realtime-sss-advances-siggraph-gdc-2025

*Researched: 2026-04-06 02:42 CDT*

# Real-Time Subsurface Scattering Advances (SIGGRAPH 2025 & GDC 2025)

## SIGGRAPH 2025 — Real-Time Subsurface Scattering Course
- **Source:** SIGGRAPH 2025 Advances in Real-Time Rendering course
- **Paper:** `advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf`
- **Key technique:** Hybrid ReSTIR-Path Tracing + Diffusion for real-time SSS
- **Claim:** Skin rendering captures "significantly more detail with much closer ground truth matching"
- **Presenters:** Part of the annual Advances course (EA/Unity/Activision presenters)

## NVIDIA RTX Skin (GDC 2025)
- First implementation of subsurface scattering in ray-traced gaming
- Part of RTX Remix technology suite
- Light transmits and scatters through skin realistically in real-time
- Built on RTX 50 Series neural rendering capabilities

## NVIDIA Neural Shading (DirectX 12 — April 2025)
- Neural shading support coming to DX12 via Agility SDK Preview
- Cooperative Vectors in HLSL enable accessing Tensor Cores from shaders
- Applications: textures, materials, lighting — all relevant to SSS implementations
- RTX Neural Texture Compression with tile-based streaming reduces memory overhead

## Key Takeaways for SOMA
1. **WebGPU parity:** DX12 Cooperative Vectors pattern could inform WebGPU compute shader approaches for SSS
2. **Hybrid diffusion + path tracing:** The SIGGRAPH 2025 hybrid approach (ReSTIR + diffusion) is the state-of-art — may be adaptable to screen-space techniques for mobile
3. **RTX Skin pattern:** NVIDIA's SSS in RTX Remix proves real-time SSS is viable in games; the diffusion approximation approach they use can be implemented in WGSL
4. **Tile-based texture streaming:** Relevant for SOMA's anatomy atlas textures on mobile — only load visible tissue layers

## Open Source Reference
- Jaysmito101/AdvancedVulkanDemos has a working SSS implementation with documentation
- GitHub resource: `github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md`


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
