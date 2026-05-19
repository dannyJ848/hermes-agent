# niivue-webgpu-medical-imaging

*Researched: 2026-04-06 18:52 CDT*

# NiiVue WebGPU Medical Imaging Exploration

**Source:** github.com/niivue/niivue-webgpu (6 stars, experimental)

## Key Findings
- NiiVue (a major open-source WebGL2 medical imaging viewer) is experimenting with WebGPU adoption
- Current approach: WebGL2 via ANGLE (supports OpenGL, DirectX, Metal, Vulkan)
- WebGPU exploration starts from Will Usher's minimal demo, gradually porting NiiVue shaders
- **Critical tradeoff:** WebGPU unlikely to ever support OpenGL-based devices — NiiVue aims to empower users without latest hardware
- WebGPU spec not yet finalized at time of exploration

## SOMA Implications
- SOMA should maintain WebGL2 fallback even if adding WebGPU features
- For medical imaging accessibility (especially in Latin America), OpenGL device support matters
- NiiVue's shader porting strategy is worth studying for SOMA's SSS shader implementation
- Volume rendering in WebGPU compute shaders remains experimental in medical context

## Related
- DECODE platform (WebGL-powered 3D viz for medical imaging)
- Kitware VolView integrating NVIDIA Clara models (browser-native imaging)
- Three.js vs WebGPU 2026: universal browser support since late 2025 for WebGPU

## Sources

- https://github.com/niivue/niivue-webgpu
- https://www.kitware.com/integrating-nvidia-clara-models-into-volview-a-technical-deep-dive/
