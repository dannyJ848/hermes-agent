# webgpu-medical-volume-path-tracing

*Researched: 2026-04-05 20:10 CDT*

# WebGPU Medical CT Volume Path Tracing (Browser-Based)

## Source
Hacker News Show HN post by MickGorobets (~Feb 2026). Also referenced: grenzwert.net

## Key Technical Details
- **GPU path tracer for volumetric medical data** running entirely in Chrome via WebGPU + WebAssembly (C++/Emscripten)
- **Delta tracking** (Woodcock null-collision algorithm) for unbiased volume rendering
- **Cook-Torrance GGX BRDF + Henyey-Greenstein phase function** — physically-based scattering
- **MacroGrid acceleration** — DDA empty-space skipping + GPU tile culling
- **Progressive frame accumulation** — noisy at first, converges to ground truth over frames
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping
- **Async mip-level streaming** with gzip decompression
- Built on **Diligent Engine** (cross-platform graphics engine with WebGPU backend)

## SOMA Relevance
- Directly applicable to SOMA's 3D anatomy viewer — WebGPU volume rendering of CT/MRI data
- Henyey-Greenstein phase function could enhance SOMA's subsurface scattering for tissue realism
- MacroGrid empty-space skipping is relevant for optimizing large anatomy datasets on mobile
- Progressive accumulation is ideal for mobile where GPU budget is limited
- Async mip-level streaming pattern could improve SOMA's asset loading

## SIGGRAPH 2025 SSS Advances (Parallel Finding)
- Hybrid ReSTIR-Path Tracing + Diffusion for real-time SSS
- Relevant for next-gen tissue rendering in anatomy apps
- Resource: https://advances.realtimerendering.com/s2025/

## Requirements
- Chrome with WebGPU enabled (other browsers limited as of early 2026)
- Discrete GPU recommended but integrated works
- C++ compiled to WASM via Emscripten


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://advances.realtimerendering.com/s2025/
- https://github.com/Jaysmito101/AdvancedVulkanDemos/blob/main/resources/subsurface_scattering.md
