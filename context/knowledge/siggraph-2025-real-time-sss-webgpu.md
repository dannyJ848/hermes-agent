# SIGGRAPH-2025-real-time-sss-webgpu

*Researched: 2026-04-05 23:37 CDT*

# SIGGRAPH 2025: Real-Time Subsurface Scattering Advances

## Key Finding
NVIDIA unveiled a **hybrid real-time subsurface scattering technique** at SIGGRAPH 2025 (August 2025, Vancouver) that combines:
- **Volumetric path tracing** for accurate light transport through translucent tissue
- **New physically-based model** for real-time skin/organ rendering

## Relevance to SOMA
- SOMA's 3D anatomy viewer currently uses a custom SSS shader approach (see `soma-sss-shaders` skill)
- NVIDIA's hybrid approach could inform a WebGPU compute-shader implementation for:
  - Realistic skin rendering (epidermis/dermis/subcutaneous layers)
  - Organ translucency (liver, kidneys, brain tissue)
  - Blood vessel subsurface glow

## Technical Details
- SIGGRAPH "Advances in Real-Time Rendering in Games" course celebrated its 20th year
- Course covers subsurface scattering + real-time path tracing innovations
- Also mentions Epic's Nanite-related patents and new mesh rendering approaches
- GPU Gems 3 Chapter 14 remains the foundational reference for real-time skin SSS

## Next Steps for SOMA
1. Monitor for NVIDIA's published slides/code from the course (usually released after SIGGRAPH)
2. Evaluate WebGPU compute shader pipeline for volumetric path tracing feasibility on mobile
3. Profile current SSS shader performance on iOS Safari to identify optimization targets
4. Consider dual-path rendering: high-quality SSS on desktop, simplified on mobile

## Sources
- SIGGRAPH 2025 Advances course: https://advances.realtimerendering.com/s2025/
- SIGGRAPH 20th anniversary: https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- GPU Gems 3 Ch.14: https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin


## Sources

- https://advances.realtimerendering.com/s2025/
- https://s2025.siggraph.org/two-decades-of-progress-in-a-frame-siggraphs-advances-in-real-time-rendering-in-games-turns-20/
- https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
