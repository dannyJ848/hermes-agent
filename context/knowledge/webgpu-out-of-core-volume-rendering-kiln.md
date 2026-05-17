# webgpu-out-of-core-volume-rendering-kiln

*Researched: 2026-04-05 14:29 CDT*

# KILN: WebGPU-Native Out-of-Core Volume Rendering

**Source:** Martin Panknin (Mar 2026) — dev.to article
**URL:** https://dev.to/mpanknin/kiln-webgpu-native-out-of-core-volume-rendering-for-multi-gb-datasets-2alb
**Live demo available** (requires WebGPU-enabled browser with 16-bit texture support)

## Key Innovation
KILN is a WebGPU-native system that streams multi-GB volumetric datasets over HTTP and renders them at interactive frame rates with a fixed, modest VRAM budget. Uses:
- **Page cache** + **virtual texture indirection** + **compute shader volume ray-marching**
- Similar to terrain virtualization in games, but applied to volumetric data
- Handles datasets too large to download in full

## Rendering Modes
- **DVR** (Direct Volume Rendering) — standard transfer-function based rendering
- **MIP** (Maximum Intensity Projection) — common in CT/MRI viewing
- **ISO** (Iso-surfaces) — surface extraction at threshold values
- Debug modes: color-coded LOD levels, indirection visualization, atlas content inspection

## Architecture Highlights
- Compute shader-based ray marching (not fragment shader)
- Progressive loading with LOD (Level of Detail) brick system
- URL-encoded rendering parameters for shareable views (camera, transfer function, settings)
- Performance panel: frame time, atlas occupancy, network throughput, loaded brick count

## Relevance to SOMA
1. **Medical imaging connection:** Volume rendering is standard in CT/MRI workstations — SOMA could eventually integrate DICOM volume viewing
2. **Mobile performance:** Out-of-core approach with fixed VRAM budget is ideal for mobile WebGPU (iOS Safari 18+ supports WebGPU)
3. **Compute shader pattern:** SOMA should consider compute shader ray marching over fragment shader approaches for better performance
4. **Progressive loading:** Bricked LOD approach could apply to SOMA's anatomy models — stream high-detail regions on demand
5. **Shareable URLs:** Good UX pattern for SOMA — encode anatomy view state in shareable links

## Technical Notes
- Requires 16-bit texture support (standard in WebGPU but worth checking on mobile)
- Volume virtualization: data is divided into bricks, only visible/needed bricks are loaded
- Indirection table maps virtual volume coordinates to physical atlas positions
- Network streaming with eviction when VRAM budget is exceeded

## Follow-Up Questions
- What brick size is optimal for mobile GPUs?
- How does KILN handle transfer function editing in real-time?
- Could this approach be combined with mesh-based anatomy rendering in SOMA?


## Sources

- https://dev.to/mpanknin/kiln-webgpu-native-out-of-core-volume-rendering-for-multi-gb-datasets-2alb
