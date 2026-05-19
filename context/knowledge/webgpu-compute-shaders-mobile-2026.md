# webgpu-compute-shaders-mobile-2026

*Researched: 2026-04-05 12:43 CDT*

# WebGPU Compute Shaders on Mobile — Status April 2026

## Key Findings

### Browser Support Landscape
- **Chrome 113+ (May 2023)**: Full WebGPU compute shader support — production-viable for GPU inference pipelines
- **Firefox**: Partial WebGPU support as of Feb 2026
- **Safari (iOS)**: **Lacks WebGPU compute shader support as of mid-2025**. This is the critical gap for SOMA's iOS target.

### Performance
- GPU-heavy workloads show **2-3x performance improvements** over WebGL equivalents when WebGPU is available
- 4-bit quantized models (Q4_0, Q4_K_M) fit in consumer mobile GPU memory
- Chrome ships built-in Gemini Nano via Prompt API (zero-setup on-device inference)

### Local-First AI Stack (Production-Ready in Chrome)
Three converged developments:
1. 4-bit quantized small language models fitting in mobile GPU memory
2. WebGPU compute shader pipelines reaching stable status
3. Chrome's built-in Gemini Nano via Prompt API

## Implications for SOMA

### Immediate (Before iOS Safari supports WebGPU compute)
- **WebGL2 fallback path mandatory** for all shader-based rendering on iOS/Safari
- Use `navigator.gpu` detection → fall back to WebGL2 GPGPU (transform feedback / texture-based compute)
- SSS shader work should be written in both WGSL (WebGPU) and GLSL (WebGL2)

### Medium-Term (When Safari ships compute shaders)
- Can unify on WGSL compute pipeline for:
  - Volume rendering (marching cubes on GPU)
  - Diffusion profile LUT generation for SSS
  - Medical image processing (windowing, segmentation)
- Expected timeline: Safari tends to ship 12-18 months after Chrome for major features

### Architecture Decision
- Implement **dual-renderer pattern**: WebGPU primary, WebGL2 fallback
- Feature detection: `if (navigator.gpu) { /* WebGPU path */ } else { /* WebGL2 path */ }`
- Share shader math/logic, differ only in API bindings

## Sources
- SitePoint (Feb 2026): "The Complete Guide to Local-First AI: WebGPU, Wasm, and Chrome's Built-in Model"
- Patel (Feb 2026): "WebGPU Accelerated Client-Side AI for Privacy Preserving Dermatological Diagnostics"
- Reddit r/GraphicsProgramming: "Is WebGPU a good choice for portable compute shaders?"

## Sources

- https://www.sitepoint.com/local-first-ai-webgpu-chrome-guide/
- https://www.researchgate.net/publication/401110730
- https://www.reddit.com/r/GraphicsProgramming/comments/1rxabei/so_is_webgpu_a_good_choice_for_portable_compute/
