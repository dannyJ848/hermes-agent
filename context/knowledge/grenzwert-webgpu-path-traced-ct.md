# grenzwert-webgpu-path-traced-ct

*Researched: 2026-04-05 15:10 CDT*

# Grenzwert: WebGPU Path-Traced Volumetric CT Rendering

**Source:** Hacker News (Mikhail Gorobets, Jan 2026), grenzwert.net
**Date:** 2026-01-28

## Summary
Grenzwert is a browser-based GPU path tracer for volumetric medical CT data, built entirely on WebGPU + WebAssembly (C++/Emscripten). It achieves ground-truth quality rendering without hardware RTX — pure compute shaders.

## Key Technical Details

### Rendering Pipeline
- **Delta tracking** (Woodcock null-collision algorithm) for unbiased volume rendering
- **Cook-Torrance GGX BRDF** + **Henyey-Greenstein phase function** for realistic light scattering
- **MacroGrid acceleration**: DDA empty-space skipping + GPU tile culling for performance
- **Progressive frame accumulation**: noisy at first, converges to ground truth
- **HDR pipeline**: bloom, auto-exposure, PBR Neutral / ACES tone mapping

### Architecture
- **C++ compiled to WebAssembly** via Emscripten — not pure JS
- Built on **Diligent Engine** (cross-platform GPU abstraction, WebGPU backend)
- **Async mip-level streaming** with gzip decompression for responsive interaction
- **3D mip pyramid** streaming: interact at low-res, progressively refine
- Transfer function editing + volume cropping in real-time

### SOMA Relevance
1. **Volume rendering pipeline applicable to anatomy**: The delta tracking + Henyey-Greenstein approach is directly usable for realistic tissue rendering (skin, fat, muscle have different scattering properties)
2. **WebGPU compute shader pattern**: No hardware RTX dependency — pure compute shaders work on any WebGPU-capable device
3. **Mip pyramid streaming**: Addresses SOMA's mobile bandwidth constraints — stream low-res first, refine on demand
4. **Diligent Engine WebGPU backend**: Could serve as a reference for SOMA's WebGPU migration path
5. **Progressive accumulation**: Matches SOMA's need for responsive interaction on mobile GPUs — show something immediately, refine over frames

### Performance Notes
- Works on discrete AND integrated GPUs
- Chrome-only currently (WebGPU requirement)
- Empty-space skipping critical for medical volumes (lots of air/background)

## Integration Path for SOMA
- Short-term: Study the delta tracking + HG phase function for SSS shader improvement
- Medium-term: Adopt mip pyramid streaming pattern for mobile anatomy datasets
- Long-term: Consider Diligent Engine or similar abstraction for WebGPU migration


## Sources

- https://news.ycombinator.com/item?id=46933474
- https://www.webgpu.com/tag/medical-visualization/
- https://grenzwert.net
