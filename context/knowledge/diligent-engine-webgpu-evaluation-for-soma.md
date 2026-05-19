# diligent-engine-webgpu-evaluation-for-soma

*Researched: 2026-04-06 01:58 CDT*

# Diligent Engine WebGPU Evaluation for SOMA

## Overview
Diligent Engine 2.5.6+ (Sept 2024) adds full WebGPU backend support, making it a candidate graphics abstraction for SOMA's 3D anatomy viewer.

## Key Features
- **Cross-platform**: D3D11, D3D12, Vulkan, OpenGL/GLES, Metal, WebGPU from single API
- **Compute shaders**: Native support via WebGPU — critical for volume rendering, SSS simulation
- **Async shader compilation**: Shaders compile in parallel, no render thread blocking
- **Lower overhead**: WebGPU reduces CPU overhead vs WebGL, more efficient GPU utilization
- **Live web samples**: Available at Diligent Engine Samples Website

## SOMA Applicability Assessment
### Pros
- Could enable WebGPU-native path tracing for CT volume rendering (replacing WebGL compute hacks)
- Single codebase for iOS (Metal), Android (Vulkan), and web (WebGPU)
- Async shader compilation would eliminate SOMA's loading freezes on mobile
- Better resource management for large anatomy meshes (memory predictability)

### Cons
- C++ core, requires Emscripten → WASM compilation (adds build complexity)
- SOMA currently Three.js/JS — would need full rewrite of rendering pipeline
- WebGPU browser support still limited (Chrome good, Safari experimental, Firefox pending)
- Significant engineering investment — not viable for current Three.js-based SOMA

## Recommendation
**Defer to SOMA v2.** Diligent Engine is overkill for the current Three.js architecture. Revisit when:
1. WebGPU has >90% browser support (project 2027)
2. SOMA needs native volume rendering (CT/MRI data)
3. Team has C++/WASM expertise

For now, continue with Three.js + custom SSS shaders (GLSL). Use WebGPU compute directly via `navigator.gpu` for specific acceleration needs (e.g., mesh decimation) without full engine swap.

## Sources
- https://diligentgraphics.com/2024/09/02/diligent-engine-2-5-6-webgpu-and-asynchronous-shaders/
- https://github.com/DiligentGraphics/DiligentEngine

## Sources

- https://diligentgraphics.com/2024/09/02/diligent-engine-2-5-6-webgpu-and-asynchronous-shaders/
- https://github.com/DiligentGraphics/DiligentEngine
