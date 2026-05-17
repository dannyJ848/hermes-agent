# webgpu-sss-medical-rendering

*Researched: 2026-04-06 18:42 CDT*

# WebGPU Subsurface Scattering for Medical Visualization

## Key Finding (SIGGRAPH 2025)
A major new SIGGRAPH 2025 paper ("Real-Time Subsurface Scattering") presents hybrid ReSTIR-path tracing + diffusion for real-time SSS. This is the state-of-the-art for real-time translucent material rendering.

## SSS Fundamentals (from MJP's reference)
- SSS occurs when light refracts into a surface, scatters among particles, and exits at a different point than it entered
- For thin/translucent materials (skin, tissue, organs), scattered light exits OUTSIDE the pixel footprint — requiring global light consideration
- Three main approaches for real-time:
  1. **Texture-space diffusion**: Render irradiance to texture, apply Gaussian blur kernels with varying widths (screen-space)
  2. **Screen-space diffusion**: Post-process blur in screen space using depth-aware kernels
  3. **Path tracing (new)**: ReSTIR-based real-time path tracing for volumetric scattering

## Application to SOMA's 3D Anatomy Viewer
- Human tissue (muscle, fat, skin, organs) all exhibit subsurface scattering
- For WebGPU implementation, screen-space diffusion is the most practical:
  - Render scene normally with G-buffer (albedo, normal, depth)
  - Apply separable Gaussian blur with tissue-specific scattering radii
  - Different tissue types = different scattering parameters (skin: broad, thin; muscle: moderate; bone: minimal)
- **WebGPU advantage**: Compute shaders allow efficient screen-space SSS passes
- The soma-sss-shaders skill already exists in the skill library for this

## References
- SIGGRAPH 2025 Advances: Real-Time Subsurface Scattering (PDF available at advances.realtimerendering.com)
- MJP's SSS Introduction: therealmjp.github.io/posts/sss-intro/
- NVIDIA GPU Gems Ch.16: Screen-space approximation techniques
- ReSTIR-Path Tracing hybrid: YouTube SIGGRAPH 2025 talk


## Sources

- https://therealmjp.github.io/posts/sss-intro/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
