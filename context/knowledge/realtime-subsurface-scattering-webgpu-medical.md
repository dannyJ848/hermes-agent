# realtime-subsurface-scattering-webgpu-medical

*Researched: 2026-04-06 16:22 CDT*

# Real-Time Subsurface Scattering for Medical 3D Visualization

## Key Techniques (from GPU Gems Ch.16 + SIGGRAPH 2025)

### 1. Wrap Lighting (Simplest Approximation)
- Modifies diffuse Lambert so light wraps beyond the terminator point
- `wrap_diffuse = max(0, (dot(L,N) + wrap) / (1 + wrap))` where wrap ∈ [0,1]
- Reduces contrast, decreasing ambient/fill light needed
- Can encode in a 1D texture indexed by dot(N,L) for GPU efficiency
- For skin: include color shift toward red near zero to simulate blood scattering

### 2. Texture-Space Diffusion (Medium Complexity)
- Render surface irradiance to a texture in UV space
- Apply Gaussian blur kernels (separable, multiple passes) to simulate light diffusion
- Different blur radii for R/G/B channels (red scatters further in skin)
- Can use summed-area tables or mipmaps for variable-radius blur

### 3. Screen-Space Subsurface Scattering (Best for Real-Time)
- Post-process effect in screen space
- Uses depth buffer to detect thin geometry (ears, nose, fingers)
- Blurs lighting with asymmetric kernels based on light direction
- Very efficient — used in AAA games and Unity/Unreal

### 4. Path Tracing SSS (SIGGRAPH 2025 Advances)
- ReSTIR-path tracing hybrid for real-time SSS
- Combines path trace light transport with diffusion profiles
- Achieves physically accurate SSS in real-time on RTX hardware
- **Not yet feasible for mobile/WebGPU** but architecture is instructive

## Application to SOMA 3D Anatomy Viewer

### Recommended Approach: Screen-Space SSS in WebGPU
For tissue visualization (skin, muscles, organs):

1. **Depth-aware blur pass**: After lighting, do a screen-space blur
2. **Thin-geometry detection**: Use depth difference to detect thin areas (ears, blood vessels)
3. **Color shift per tissue type**: Different scatter profiles for skin (red shift), muscle (dark red), fat (yellow-white)
4. **Fallback for non-WebGPU**: Use wrap lighting in WebGL2

### Implementation Sketch (WGSL)
```wgsl
// Wrap lighting in fragment shader
fn wrap_diffuse(N: vec3f, L: vec3f, wrap: f32) -> f32 {
  return max(0.0, (dot(N, L) + wrap) / (1.0 + wrap));
}

// Screen-space SSS: sample neighbors along light direction
fn sss_scatter(uv: vec2f, light_dir: vec2f, radius: f32) -> vec3f {
  let sss_color = vec3f(
    gaussianBlur(uv, light_dir, radius * 1.0),  // R - scatters most
    gaussianBlur(uv, light_dir, radius * 0.6),  // G
    gaussianBlur(uv, light_dir, radius * 0.3),  // B - scatters least
  );
  return sss_color;
}
```

### Priority: LOW-MEDIUM
Wrap lighting is trivial to add (1 line change in fragment shader). Screen-space SSS is a post-processing pass requiring WebGPU. Path-traced SSS is not mobile-viable yet.

## Sources
- NVIDIA GPU Gems Chapter 16: https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- SIGGRAPH 2025 Advances: Real-Time Subsurface Scattering course
- WebGPU for Medical AI (ResearchGate, 2026) — dermatological diagnostics with WebGPU acceleration


## Sources

- https://developer.nvidia.com/gpugems/gpugems/part-iii-materials/chapter-16-real-time-approximations-subsurface-scattering
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
