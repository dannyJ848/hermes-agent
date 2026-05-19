# webgpu-medical-sss-2025

*Researched: 2026-04-06 05:13 CDT*

# WebGPU + SSS for Medical Visualization (2025-2026)

## Key Findings from SIGGRAPH 2025 & Khronos Events

### SIGGRAPH 2025: Real-Time Subsurface Scattering
- **Source**: advances.realtimerendering.com/s2025 — full course on real-time SSS
- **Key advance**: Hybrid ReSTIR-Path Tracing + Diffusion for real-time SSS
- Novel hybrid solution combining path tracing with diffusion approximation
- Applicable to skin, organ tissue, and translucent anatomical structures
- **SOMA relevance**: Directly applicable to realistic tissue rendering in 3D anatomy viewer

### Khronos "3D on the Web" Event (GDC 2025, March 19)
- Talk: "Large Scale Scientific Visualization with WebGL, WebGPU"
- WebGPU maturing for scientific/medical visualization workloads
- Browser-native GPU compute enables complex medical rendering without plugins

### WebGPU Accelerated Client-Side AI (Feb 2026)
- Paper by Arpankumar Patel on ResearchGate
- WebGPU for privacy-preserving dermatological diagnostics
- Client-side AI inference with local differential privacy
- **SOMA relevance**: Pattern for running AI diagnostics directly in browser via WebGPU — could enable offline anatomy quiz grading, lesion detection on 3D models

### NVIDIA GPU Gems Chapter 16 (Classic Reference)
- Real-time SSS approximations for skin/marble using programmable shaders
- Wrap lighting, thickness-based transmission, texture-space diffusion
- Still relevant for mobile-friendly SSS where full path tracing is too expensive

## Actionable for SOMA
1. **SSS shader priority**: Start with GPU Gems wrap-lighting approach (cheapest), graduate to texture-space diffusion
2. **WebGPU migration**: Monitor Khronos WebGPU stability — plan SOMA renderer migration from WebGL
3. **Client-side AI**: WebGPU compute shaders could enable on-device medical AI without server dependency
4. **Hybrid path tracing**: ReSTIR technique may become feasible on mobile GPUs within 2 years


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://www.youtube.com/watch?v=AtFBbMnUgoc
- https://www.youtube.com/watch?v=HzcFzCkt5aU
- https://www.researchgate.net/publication/401110730
- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-subsurface-scattering
