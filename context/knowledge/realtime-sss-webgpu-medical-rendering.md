# realtime-sss-webgpu-medical-rendering

*Researched: 2026-04-06 00:16 CDT*

# Real-Time Subsurface Scattering for Medical Visualization

## Key Findings (April 2026 Research)

### SIGGRAPH 2025 Advances: Hybrid ReSTIR-Path Tracing + Diffusion
- Novel hybrid approach combining ReSTIR path tracing with diffusion theory for real-time SSS
- Source: `advances.realtimerendering.com/s2025` — SIGGRAPH 2025 Advances course
- Key technique: hybridizes Monte Carlo path tracing with analytical diffusion approximation
- Directly applicable to WebGPU compute shaders for anatomical tissue rendering

### WebGPU + Medical AI (Feb 2026 Paper)
- Patel (2026): "WebGPU Accelerated Client-Side AI for Privacy Preserving Dermatological Diagnostics"
- Uses WebGPU for both AI inference AND rendering on client side
- Demonstrates WebGPU is production-ready for medical imaging in browser
- Local differential privacy integration for patient data protection

### GPU Gems Classic Techniques (Still Relevant)
- **Wrap Lighting**: `max(0, (dot(L,N) + wrap) / (1+wrap))` — cheapest SSS approximation
- **Texture-based approach**: Encode diffuse wrap function + color shift (→red) in 1D texture
- **Depth-mapped scattering**: Render thickness map, use to modulate scatter intensity
- For skin: color shifts toward red in shadow transitions (blood/tissue absorption)
- Most visible where tissue is thin (ears, nostrils — analogous to organ membranes in anatomy)

### Application to SOMA 3D Anatomy Viewer
1. **Tier 1 (mobile-safe)**: Wrap lighting + texture-based color shift — runs on any GPU
2. **Tier 2 (WebGPU)**: Screen-space diffusion approximation using thickness map
3. **Tier 3 (future)**: ReSTIR-based path tracing for photorealistic tissue rendering
- Start with Tier 1 wrap lighting in existing Three.js shader material
- SSS most impactful for: skin layers, organ surfaces, vascular structures

### Khronos GDC 2025: Large Scale Scientific Visualization
- Khronos "3D on the Web" event (March 2025) covered WebGL/WebGPU scientific viz
- WebGPU compute shaders now viable for real-time volume rendering in browser

## Sources
- SIGGRAPH 2025 Advances course: https://advances.realtimerendering.com/s2025/
- GPU Gems Ch.16: https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- Patel 2026 WebGPU Medical: https://www.researchgate.net/publication/401110730
- Khronos GDC 2025: https://www.youtube.com/watch?v=HzcFzCkt5aU

## Sources

- https://advances.realtimerendering.com/s2025/
- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://www.researchgate.net/publication/401110730
