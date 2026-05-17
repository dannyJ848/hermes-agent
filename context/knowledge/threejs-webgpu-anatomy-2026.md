# threejs-webgpu-anatomy-2026

*Researched: 2026-04-05 12:34 CDT*

# Three.js WebGPU Renderer for Anatomy Visualization (April 2026)

## Summary
Three.js is actively transitioning to a WebGPU renderer backend in 2026, with significant implications for SOMA's 3D anatomy viewer. The ecosystem is split between WebGL (mature, universal) and WebGPU (performance-critical edge cases).

## Key Findings

### Three.js WebGPU Status (April 2026)
- **TSL (Three Shading Language)** is the new abstraction layer for WebGPU shaders in Three.js, replacing raw WGSL/GLSL
- WebGPU renderer shows mixed performance: excels at GPU-driven techniques (instancing, GPGPU particles, compute shaders) but can underperform WebGL for simple scenes due to driver overhead
- Community consensus: WebGPU is NOT a blanket upgrade — it wins for specific patterns (compute shaders, large instancing, SSS)

### Anatomy-Specific Three.js Projects
- **Interactive 3D Anatomy by Layers**: A Three.js forum project (discourse.threejs.org/t/88813) demonstrates anatomical layer exploration — highlighting selected organs/systems, color changes for visualization, and interactive controls (rotate, zoom, pan). Directly relevant to SOMA's layered anatomy approach.

### Performance Best Practices (2026)
- GPU-driven rendering over CPU scene graphs
- Instancing for repeated anatomical structures
- LOD (Level of Detail) essential for mobile
- Texture compression (Basis Universal / KTX2) for mobile delivery

### Three.js vs Native WebGPU
- Three.js remains better for general-purpose visualization (SOMA's use case)
- Native WebGPU only justified for extreme performance requirements
- Recommendation: Stay on Three.js but plan for WebGPU renderer migration

## SOMA Impact
- **Short-term**: Continue with Three.js WebGL renderer, adopt KTX2 texture compression
- **Medium-term**: Migrate to TSL-based shaders for SSS (subsurface scattering) — more portable across WebGL/WebGPU
- **Long-term**: Full WebGPU renderer adoption once mobile Safari support matures
- **Architecture**: Use GPU-driven instancing for repeated anatomical structures (vertebrae, teeth, blood vessels)

## Sources
- Reddit: Three.js 2026 community discussion
- Altersquare: Three.js vs WebGPU for large-scale viewers
- Three.js Forum: WebGPU performance issues
- Utsubo: 100 Three.js performance tips (2026)
- Three.js Forum: 3D Interactive Anatomy by Layers

## Sources

- https://www.reddit.com/r/threejs/comments/1qqdm49/threejs_in_2026_and_beyond_where_do_you_think_its/
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://discourse.threejs.org/t/webgpu-performance-issue/87939
- https://www.utsubo.com/blog/threejs-best-practices-100-tips
- https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813
