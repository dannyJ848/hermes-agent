# webgpu-subsurface-scattering-techniques-2025

*Researched: 2026-04-05 17:58 CDT*

# WebGPU Subsurface Scattering for Medical Anatomy Rendering

## Key Finding (April 2026)

SIGGRAPH 2025 "Advances in Real-Time Rendering" course features a brand-new chapter on real-time subsurface scattering (SSS) via hybrid ReSTIR-Path Tracing & Diffusion. This represents the state of the art for real-time SSS.

## Classical Approaches (Still Relevant for WebGPU)

### 1. Separable Subsurface Scattering (d'Eon & Luebke, GPU Gems 3 Ch.14)
- Decompose 2D diffusion into two 1D passes (horizontal + vertical blur)
- Uses Gaussian profiles approximating skin's multi-layer scattering
- **Performance:** O(n) per pass, very fast on modern GPUs
- **WebGPU viability:** EXCELLENT — separable blur is trivial in compute shaders
- 6% of light is specular (surface reflectance), rest enters subsurface layers
- Skin modeled with multiple scattering profiles per wavelength

### 2. Pre-Integrated Skin Shading (Penner & Borshukov)
- Approximate scattering with a texture lookup based on curvature and N·L
- No blur passes needed — single shader evaluation
- **WebGPU viability:** BEST for mobile — no extra render targets
- Trade-off: less accurate than separable but much cheaper

### 3. Screen-Space Subsurface Scattering (Jimenez et al.)
- Apply SSS as a screen-space post-process
- Uses judiciously chosen Gaussian kernels
- **WebGPU viability:** GOOD — needs screen-space textures

## SIGGRAPH 2025 Advances
- Hybrid ReSTIR path tracing + diffusion for RT SSS
- Works with ray tracing pipelines (RT cores)
- **WebGPU viability:** LIMITED — WebGPU ray tracing not yet widely available
- But the diffusion fallbacks are still applicable

## Recommendations for SOMA
1. **Start with Pre-Integrated SSS** for mobile performance
2. **Upgrade to Separable SSS** when desktop/WebGPU compute is available
3. **Key parameters:** scatter radius (~0.005-0.01 for skin), diffusion profile texture
4. **Tissue-specific profiles:** different scatter params for skin vs muscle vs organ tissue
5. GLSL/WGSL shaders available at: https://github.com/Jaysmito101/AdvancedVulkanDemos

## Sources
- SIGGRAPH 2025 Advances course: https://advances.realtimerendering.com/s2025/
- GPU Gems 3 Ch.14 (d'Eon & Luebke): https://developer.nvidia.cn/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin


## Sources

- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://developer.nvidia.cn/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- https://github.com/Jaysmito101/AdvancedVulkanDemos
