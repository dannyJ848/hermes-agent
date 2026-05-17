# SIGGRAPH-2025-realtime-SSS-techniques

*Researched: 2026-04-05 17:28 CDT*

# SIGGRAPH 2025: Advances in Real-Time Subsurface Scattering

**Date:** August 2025, Vancouver Convention Centre

## Key Finding
NVIDIA unveiled a **hybrid real-time subsurface scattering (SSS) technique** at SIGGRAPH 2025's "Advances in Real-Time Rendering in Games" course (20th anniversary edition). The technique combines:

1. **Volumetric path tracing** — for accurate light transport through translucent materials
2. **New physically-based SSS model** — artist-friendly parameters while maintaining physical accuracy

## Sources
- Official PDF: `advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf` (binary, not text-extractable)
- CGW coverage: NVIDIA's hybrid technique specifically mentioned as combining volumetric path tracing + new PBR SSS
- ACM DOI: `10.1145/3721241.3744991` (Advances in Real-Time Rendering Part II)
- Reddit r/GraphicsProgramming discussion confirms production SSS focus

## Relevance to SOMA
SOMA's 3D anatomy viewer currently uses custom WGSL SSS shaders (see `soma-sss-shaders` skill). NVIDIA's hybrid approach could inform:
- Better skin rendering on anatomical models
- Translucency for organ tissues (ears, nasal septum, eyelids)
- Potential WebGPU implementation paths since the technique targets real-time game rendering

## Next Steps
- Monitor for open-source implementations or shader code releases
- Check if the technique is compatible with WebGPU compute shaders
- Compare against SOMA's current separable SSS implementation


## Sources

- https://www.cgw.com/Press-Center/Siggraph/2025/Two-decades-of-progress-in-a-frame-SIGGRAPH-s-Adv.aspx
- https://dl.acm.org/doi/10.1145/3721241.3744991
- https://www.reddit.com/r/GraphicsProgramming/comments/1pz08h6/siggraph_2025_advances_in_realtime_rendering_in/
