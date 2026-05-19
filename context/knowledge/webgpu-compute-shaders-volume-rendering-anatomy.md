# webgpu-compute-shaders-volume-rendering-anatomy

*Researched: 2026-04-05 16:44 CDT*

# WebGPU Compute Shaders for Medical Volume Rendering

**Date:** 2026-04-05
**Relevance:** SOMA 3D anatomy viewer — potential rendering pipeline upgrade after WebGPU migration

## Key Findings

### 1. WebGPU Compute Rasterizers — 10x Faster for Dense Geometry
OmarShehata's step-by-step guide ([webgpu-compute-rasterizer](https://github.com/OmarShehata/webgpu-compute-rasterizer)) demonstrates building a full rasterizer using WebGPU compute shaders. Key insights:
- **Point cloud rendering:** Markus Schütz's research shows compute shader rendering of >100M points is ~10x faster than point primitives
- **Custom pixel blending:** Compute shaders allow reading AND writing to the same buffer simultaneously — enables techniques impossible in traditional graphics pipeline (e.g., averaging all points on same pixel for volume-like visualization, "X-ray" effects)
- **Atomic operations:** WebGPU provides `atomicAdd`, `atomicMax`, etc. for coordinating pixel writes across workgroups
- **UE5 pattern:** Unreal Engine 5 switches to compute rasterizer for very small triangles (nanite-like) — directly relevant for dense medical meshes

**SOMA application:** Anatomy models often have dense triangle meshes (>500K triangles). Compute shader rasterization could enable:
- Efficient rendering of high-resolution anatomical structures on mobile
- Custom cross-section blending for translucent tissue layers
- Volume-averaged X-ray visualization mode

### 2. WebGPU Path Tracer — Real-Time Ray Bouncing
gnikoloff's [webgpu-raytracer](https://github.com/gnikoloff/webgpu-raytracer) implements real-time path tracing via compute shaders:
- **BVH acceleration:** Uses bounding volume hierarchy for efficient ray-scene intersection
- **Multi-bounce:** Compute shader bounces rays through scene gathering color/illumination
- **Architecture:** TypeScript + Vite (matches SOMA's stack)
- **Requirement:** Requires powerful GPU (desktop-class); mobile support noted as limited

**SOMA application:** BVH-based ray intersection could power:
- Interactive cross-section cutting with real-time edge rendering
- Subsurface scattering via volumetric path tracing (connecting to SIGGRAPH 2025 hybrid ReSTIR findings from cycle 210)
- Accurate shadow casting for depth perception in anatomy visualization

### 3. WebGPU Volume Rendering Framework (MDPI 2025)
An MDPI Applied Sciences paper (doi: 10.3390/app15252782) proposes a WebGPU-based volume rendering framework for interactive visualization of scalar data — while focused on ocean data, the technique directly transfers to medical volumetric data (CT/MRI slices).
- **Fragment shader ray marching:** Full-screen triangle approach for direct volume rendering
- **Interactive framerates:** Reported smooth interaction with large scalar datasets

### 4. Medical-Specific WebGPU Applications (2025-2026)
- **WebGPU + Client-Side AI for Dermatology** (Patel, Feb 2026): Uses WebGPU compute for on-device skin lesion classification with local differential privacy — proves WebGPU compute is viable for privacy-preserving medical AI
- **WebGPU MRI Pipeline** (LinkedIn, Beckley): Building MRI reverse engineering pipeline with Phong reflection in WebGPU for patient brain digital twins
- **Mol* Molecular Graphics Engine** (Rose, 2026, Protein Science): Announcing WebGPU migration for GPU-accelerated molecular visualization — same migration path SOMA is taking

## Architecture Recommendation for SOMA

### Phase 1 (Current — WebGL):
- Use Three.js built-in SubsurfaceScatteringShader addon (from cycle 211 finding)
- Standard rasterization pipeline

### Phase 2 (WebGPU Migration — Three.js r171+):
- Switch to WebGPURenderer (zero-config in r171)
- Implement compute shader rasterizer for dense anatomy meshes
- Add BVH-based ray intersection for cross-section rendering

### Phase 3 (Advanced — Compute Shader Volume Rendering):
- Port ray-marching volume renderer for CT/MRI slice data
- Implement hybrid ReSTIR SSS (from SIGGRAPH 2025 finding)
- Add volume-averaged X-ray visualization mode

## Resources
- Compute rasterizer tutorial: https://github.com/OmarShehata/webgpu-compute-rasterizer
- WebGPU raytracer: https://github.com/gnikoloff/webgpu-raytracer
- WebGPU native volume rendering: https://github.com/samdauwe/webgpu-native-examples


## Sources

- https://github.com/OmarShehata/webgpu-compute-rasterizer
- https://github.com/gnikoloff/webgpu-raytracer
- https://www.mdpi.com/2076-3417/15/5/2782
- https://www.researchgate.net/publication/401110730
- https://github.com/samdauwe/webgpu-native-examples
