# webgpu-sss-medical-viz-2025

*Researched: 2026-04-06 03:13 CDT*

# WebGPU Subsurface Scattering for Medical Visualization (2025-2026)

## Key Developments

### SIGGRAPH 2025: Real-Time SSS via Hybrid ReSTIR-Path Tracing & Diffusion
- **Source**: SIGGRAPH 2025 Advances in Real-Time Rendering course
- Novel hybrid approach combining ReSTIR path tracing with diffusion approximation for real-time subsurface scattering
- Represents state-of-the-art in real-time SSS — previously path tracing was too expensive for real-time
- **SOMA relevance**: Could replace our current screen-space SSS approximation with a more physically accurate approach once WebGPU compute shaders support this pattern

### WebGPU for Scientific Visualization (Khronos GDC 2025)
- Khronos "3D on the Web" event (March 2025, San Francisco)
- Large-scale scientific visualization demonstrated with WebGL + WebGPU + WebAssembly pipeline
- Shows WebGPU is production-ready for complex medical/scientific rendering
- **SOMA relevance**: Validates our WebGPU migration path for the anatomy viewer

### WebGPU Client-Side AI for Dermatological Diagnostics (Feb 2026)
- Privacy-preserving skin diagnostics running entirely client-side via WebGPU
- Combines WebGPU compute with local differential privacy
- **SOMA relevance**: Architecture pattern for SOMA — run AI diagnostics on-device using WebGPU, no cloud dependency

### GPU Gems Ch.16: Real-Time SSS Approximations (NVIDIA)
- Classic reference for screen-space SSS using texture-space diffusion
- Wrap lighting + thickness maps for real-time translucency
- Still the most practical approach for mobile/WebGPU today

## SOMA Integration Notes
1. **Short-term**: Continue with screen-space SSS (GPU Gems approach) — well-understood, mobile-friendly
2. **Medium-term**: Watch for WebGPU compute shader implementations of ReSTIR-SSS
3. **Architecture**: WebGPU + WASM pipeline for large anatomy datasets (confirmed viable by Khronos demo)
4. **Privacy angle**: WebGPU on-device inference for medical diagnostics is an emerging pattern

## Sources
- SIGGRAPH 2025: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- Khronos GDC 2025: https://www.youtube.com/watch?v=HzcFzCkt5aU
- WebGPU Dermatology (2026): https://www.researchgate.net/publication/401110730
- GPU Gems Ch.16: https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering

## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.youtube.com/watch?v=HzcFzCkt5aU
- https://www.researchgate.net/publication/401110730
