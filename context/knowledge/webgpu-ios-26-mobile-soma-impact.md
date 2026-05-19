# webgpu-ios-26-mobile-soma-impact

*Researched: 2026-04-06 01:16 CDT*

# WebGPU on iOS 26 Safari — Impact on SOMA

## Key Finding (Aug 2025, confirmed Jan 2026)
- **WebGPU achieved full cross-browser support January 2026** (Firefox 147 was last holdout)
- **iOS 26 Safari ships full WebGPU** including compute shaders, memory buffers, and GPU-accelerated pipelines
- Apple's implementation builds atop Metal — high performance with minimal battery impact
- Unifies Apple ecosystem: macOS, iOS, iPadOS, visionOS all support WebGPU
- 70%+ browser support globally, 15x performance gains over WebGL

## Compute Shader Capabilities Now Available on Mobile
- GPU-accelerated video rendering and effects
- Real-time AI inference in-browser
- Advanced 3D rendering with modular pipelines
- GPU textures replacing CPU-side memory copies (faster, more efficient)
- Low-level GPU access comparable to Metal/DirectX 12

## Impact on SOMA Architecture
1. **SSS Shaders**: Can now implement real subsurface scattering via compute shaders on iOS, not just the wrap-lighting approximation
2. **Medical Image Processing**: GPU-accelerated DICOM/CT slice rendering in-browser
3. **Performance**: Can replace WebGL2 fallback paths with native WebGPU for 15x performance gain
4. **Architecture Decision**: Design dual-path renderer — WebGPU primary (compute SSS, GPU particles), WebGL2 fallback
5. **Deployment**: iOS 26+ users get full fidelity; older iOS falls back to WebGL2 approximations

## Action Items for SOMA
- Audit current Three.js/WebGL2 code for WebGPU migration points
- Implement WebGPU compute shader SSS prototype (reference: soma-sss-shaders skill)
- Add feature detection: `navigator.gpu` → WebGPU path, else WebGL2 path
- Test on iOS 26 Safari beta for performance benchmarks
- Consider WebGPU-only features: GPU-accelerated cross-section computation, real-time tissue deformation

## Sources
- https://appdevelopermagazine.com/webgpu-in-ios-26/
- https://web.dev/blog/webgpu-supported-major-browsers
- https://byteiota.com/webgpu-2026-70-browser-support-15x-performance-gains/


## Sources

- https://appdevelopermagazine.com/webgpu-in-ios-26/
- https://web.dev/blog/webgpu-supported-major-browsers
- https://byteiota.com/webgpu-2026-70-browser-support-15x-performance-gains/
