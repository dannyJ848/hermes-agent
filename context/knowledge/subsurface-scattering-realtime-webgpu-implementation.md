# subsurface-scattering-realtime-webgpu-implementation

*Researched: 2026-04-05 14:49 CDT*

# Subsurface Scattering (SSS) Real-Time Implementation Patterns (2025)

## Source: Evergine Engine SSS Implementation (March 2025)
Reference: Jorge Jimenez's separable SSS solution.

### Two-Component Architecture
1. **Transmittance (Translucency):** Uses shadow map depth to estimate surface thickness at each pixel. Calculates how much light passes through thin areas (ears, nostrils). Distance limit + gradient function to tint the transmitted light.

2. **Diffuse Blur (SSSBlur):** Compute shader that applies screen-space diffuse blur using a diffusion profile. Two passes: horizontal then vertical separable blur. Uses normal texture, depth, and camera FOV. Strength stored in GBuffer's Distortion attachment (B channel).

### Key Parameters
- **SSS Scatter** (default 0.045): Maximum distance light can scatter through surface
- Separate scatter distances per RGB channel (skin has different scattering for red/green/blue)

### Relevance to SOMA
- This separable blur approach is GPU-efficient and works in real-time
- Could be adapted for WebGPU compute shaders in Three.js
- The shadow-map-based thickness estimation is the key insight for translucency in anatomy viewers
- The GBuffer approach (storing SSS strength in a channel) integrates cleanly into deferred rendering

### Implementation Path for SOMA
1. Use WebGPU compute shaders for the SSSBlur passes
2. Shadow map already available from directional light in Three.js
3. Profile: skin diffusion profile (more red scattering = larger red scatter distance)
4. Parameters exposed as uniforms for per-organ customization


## Sources

- https://evergine.com/subsurface-scattering-sss-evergine/
- https://blog.maximeheckel.com/posts/field-guide-to-tsl-and-webgpu/
