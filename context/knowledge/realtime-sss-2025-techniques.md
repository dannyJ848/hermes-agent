# realtime-sss-2025-techniques

*Researched: 2026-04-05 22:22 CDT*

# Real-Time Subsurface Scattering: 2025 State of the Art

## Key Developments (SIGGRAPH 2025 Advances Course)

### 1. Hybrid ReSTIR-Path Tracing + Diffusion for SSS
- SIGGRAPH 2025 "Advances in Real-Time Rendering" course includes a dedicated SSS session
- Novel hybrid solution combining ReSTIR path tracing with diffusion approximation for real-time SSS
- Claims significantly more detail capture with closer ground truth matching than prior methods
- Source: `advances.realtimerendering.com/s2025` (full PDF available but binary)

### 2. NVIDIA RTX Skin (GDC 2025)
- One of the first implementations of SSS in ray-traced gaming
- Part of RTX Remix toolkit — light transmits through skin surfaces realistically
- Uses RTX Neural Shaders — small neural networks inside programmable shaders
- **DirectX 12 support via Agility SDK Preview (April 2025)** — Cooperative Vectors in HLSL enable Tensor Core access from shaders
- This is HUGE for WebGPU: the neural shader pattern (small NN inside shader) maps directly to WebGPU compute/compute-bind-group patterns

### 3. Neural Shading Architecture
- NVIDIA RTX Neural Shaders: neural networks embedded in shader pipeline
- Applications: textures, materials, lighting — broad scope
- Cooperative Vectors in DirectX enable matrix-vector operations from within shaders
- For SOMA: we can implement lightweight SSS neural approximations in WGSL compute shaders

### 4. RTX Texture Streaming SDK
- Tile-based texture streaming — decompress only accessed portions
- Relevant for anatomical texture atlases in SOMA — medical models have huge texture maps
- Could inform LOD strategy for mobile anatomy viewer

### 5. ReSTIR PT (Path Tracing) + Mega Geometry
- ReSTIR PT + ReSTIR DI for real-time path tracing with SSS
- RTX Mega Geometry enables ray tracing with extreme geometric complexity (millions of triangles)
- Demonstrated in "Zorah" demo using Unreal Engine 5 NvRTX branch

## SOMA Architecture Implications

### WebGPU-Compatible SSS Approaches (ranked by feasibility)
1. **Screen-space SSS (Christensen & Hammersley approximation)** — Already partially implemented in soma-sss-shaders skill
2. **Neural SSS in WGSL compute** — Small MLP (3-4 layers, 32-wide) evaluating per-pixel scattering; maps to WebGPU compute shader pattern inspired by NVIDIA's neural shader approach
3. **Pre-integrated SSS (Penner & Borshukov)** — Lookup texture approach, mobile-friendly
4. **Diffusion-profile approximation (Jimenez et al.)** — Gaussian sum fitting, screen-space blur passes

### Key Takeaway
The 2025 trend is **neural approximations inside the rendering pipeline** rather than pure analytical models. For SOMA's WebGPU renderer, implementing a small neural SSS evaluator in a compute shader (inspired by NVIDIA's cooperative vectors concept) could provide better quality than screen-space blur at similar performance cost on modern GPUs.

## Sources
- SIGGRAPH 2025 Advances in Real-Time Rendering: `advances.realtimerendering.com/s2025`
- NVIDIA RTX Blog (GDC 2025): `developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/`
- Jaysmito101 Vulkan SSS demos: `github.com/Jaysmito101/AdvancedVulkanDemos`


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/blog/nvidia-rtx-advances-with-neural-rendering-and-digital-human-technologies-at-gdc-2025/
- https://www.reddit.com/r/GraphicsProgramming/comments/1lfku5c/playing_around_with_realtime_subsurface/
