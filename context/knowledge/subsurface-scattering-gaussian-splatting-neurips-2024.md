# subsurface-scattering-gaussian-splatting-neurips-2024

*Researched: 2026-04-05 20:04 CDT*

# Subsurface Scattering for Gaussian Splatting (NeurIPS 2024)

**Authors:** Jan-Niklas Dihlmann, Arjun Majumdar, Andreas Engelhardt, Raphael Braun, Hendrik PA Lensch

## Key Innovation
Extends 3D Gaussian Splatting to handle subsurface scattering materials by decomposing the scene into:
1. **Explicit surface** — 3D Gaussians with spatially varying BRDF
2. **Implicit volumetric representation** — captures the scattering component
3. **Learned incident light field** — accounts for shadowing

All parameters optimized jointly via ray-traced differentiable rendering.

## Capabilities
- Material editing at interactive rates
- Relighting with novel view synthesis
- Works on both synthetic data and real multi-view multi-light captures (light-stage setup)

## Relevance to SOMA
- **Anatomy rendering:** Biological tissues are prime candidates for SSS (skin, organs, muscles all exhibit subsurface scattering)
- **WebGPU potential:** Gaussian Splatting runs at interactive rates — could be adapted for WebGPU-based anatomy viewer
- **BRDF editing:** Could allow users to adjust tissue material properties (e.g., toggle between healthy/ pathologies appearance)
- **Multi-light dataset:** Their light-stage acquisition pipeline could inform SOMA's 3D anatomy asset creation

## Performance
"Comparable or better results at a fraction of optimization and rendering time" vs. prior work.

## Sources
- NeurIPS 2024 Poster #96787
- SIGGRAPH 2025 Advances course on Real-Time Subsurface Scattering also identified (PDF binary — content not extractable but references known techniques from GPU Gems 3 Ch.14)
- Jaysmito101/AdvancedVulkanDemos GitHub has SSS implementation reference

## Sources

- https://neurips.cc/virtual/2024/poster/96787
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- https://github.com/Jaysmito101/AdvancedVulkanDemos
