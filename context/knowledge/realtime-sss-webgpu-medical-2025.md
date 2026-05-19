# realtime-sss-webgpu-medical-2025

*Researched: 2026-04-06 19:37 CDT*

# Real-Time Subsurface Scattering for Medical Visualization (2025-2026)

## Key Developments

### SIGGRAPH 2025: Advances in Real-Time Subsurface Scattering
- **Source:** SIGGRAPH 2025 Advances in Real-Time Rendering course
- **Key technique:** ReSTIR-Path Tracing combined with diffusion profiles for real-time SSS
- **Relevance to SOMA:** Directly applicable to tissue rendering in anatomy viewer
- **URL:** https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- **YouTube talk:** "RT Subsurface Scattering via Hybrid RESTIR-Path Tracing" - covers combining path trace light transport with diffusion profiles for realistic SSS in real-time

### WebGPU for Privacy-Preserving Medical AI (Feb 2026)
- **Paper:** "WebGPU Accelerated Client-Side AI for Privacy Preserving Dermatological Diagnostics: Performance Benchmarking and Local Differential Privacy Integration"
- **Author:** Arpankumar Patel (Feb 2026)
- **Key insight:** WebGPU enables client-side medical AI inference, avoiding server-side data transfer
- **Relevance to SOMA:** Validates WebGPU as viable platform for medical apps; privacy-preserving approach aligns with SOMA's offline-first architecture

### Large Scale Scientific Visualization with WebGL/WebGPU (2025)
- **YouTube:** "Large Scale Scientific Visualization with WebGL, WebGPU & WebAssembly" at 3D on the Web 2025
- **Relevance:** Demonstrates WebGPU's capability for large-scale 3D scientific data

## Application to SOMA Architecture

### Priority Rendering Techniques to Implement:
1. **Diffusion Profile SSS** — Pre-computed diffusion profiles for skin/muscle tissue (lightweight, mobile-friendly)
2. **ReSTIR-style importance sampling** — If targeting higher-end devices, path-traced SSS with resampling
3. **Separable SSS** — Screen-space technique, 2-pass Gaussian blur approximating diffusion (best for mobile WebGPU)

### Recommended SOMA SSS Pipeline:
1. Start with **Separable Subsurface Scattering** (GPU Gems 3 Ch.16 approach)
2. Port to WebGPU compute shaders
3. Use pre-integrated skin shading for mobile fallback
4. Consider ReSTIR for desktop/tablet quality mode

## Sources
- SIGGRAPH 2025 SSS course: https://advances.realtimerendering.com/s2025/
- WebGPU Medical AI (Patel 2026): https://www.researchgate.net/publication/401110730
- GPU Gems 3 Ch.16: https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering


## Sources

- https://advances.realtimerendering.com/s2025/
- https://www.researchgate.net/publication/401110730
- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://www.youtube.com/watch?v=AtFBbMnUgoc
