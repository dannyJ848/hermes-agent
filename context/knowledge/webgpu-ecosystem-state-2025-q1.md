# webgpu-ecosystem-state-2025-q1

*Researched: 2026-04-06 00:40 CDT*

# WebGPU Ecosystem State — Q1 2025

## Key Takeaway
WebGPU is production-ready for interactive 3D in the browser. Multiple demos prove near-desktop-quality visuals with compute shaders, fluid simulation (300k+ particles), and AI inference — all client-side.

## Projects Relevant to SOMA

### 1. Utsubo Interactive Portfolio
- **Tech:** Three.js WebGPURenderer
- **Demo:** Fully interactive 3D cheetah moving through scenes with real-time lighting
- **Key for SOMA:** Proves Three.js WebGPURenderer is viable for complex anatomical models. WebGL fallback available for older browsers.
- **URL:** www.utsubo.com

### 2. Slime Mold Simulation (Suboptimal Engineer)
- **Tech:** WebGPU Compute Shaders + TypeScript
- **Key for SOMA:** Demonstrates compute shader pattern for particle-based systems. Same architecture could drive tissue simulation or anatomical deformation in SOMA.
- **URL:** GitHub (Suboptimal Engineer)

### 3. MLS-MPM Fluid Simulation (Matsuoka_601)
- **Tech:** MLS-MPM (Moving Least Squares Material Point Method) via WebGPU
- **Performance:** 300k particles on mid-range GPUs, real-time
- **Key for SOMA:** Fluid simulation techniques applicable to blood flow visualization, surgical simulation. MLS-MPM allows larger timesteps than SPH.

### 4. WebGPU + Transformers.js (Local AI Inference)
- **Key for SOMA:** On-device AI for medical terminology lookup, bilingual NLP (EN/ES), and anatomy quiz generation — all running client-side without server dependency.

### 5. Realishot (3D Rendering Tool)
- Online 3D rendering tool using WebGPU — proves browser-based 3D production workflows are viable.

## wgpu v28 (Rust)
- Released with **mesh shader support** — critical for LOD systems
- Mesh shaders replace traditional vertex shader pipeline with flexible meshlet-based rendering
- **SOMA Impact:** Could enable GPU-driven mesh decimation for anatomy LOD without CPU bottleneck. Currently wgpu-side; WebGPU spec adoption pending.

## Architecture Implications for SOMA
1. **Three.js WebGPURenderer** is the migration path from current WebGL setup
2. **Compute shaders** enable: tissue deformation, fluid sim, mesh decimation — all on GPU
3. **Mesh shaders** (wgpu v28) will eventually enable GPU-driven LOD for anatomy models
4. **On-device AI** via Transformers.js could power bilingual medical NLP without network calls


## Sources

- https://www.webgpuexperts.com/best-webgpu-updates-january-2025
- https://www.reddit.com/r/rust/comments/1ppgxyl/wgpu_v28_released_mesh_shaders_immediates_and/
