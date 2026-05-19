# threejs-webgpu-clipping-planes-status

*Researched: 2026-04-05 21:55 CDT*

# Three.js WebGPU Clipping Planes & Renderer Status (April 2026)

## Key Findings

### WebGPU Clipping Planes
- Three.js has an official WebGPU clipping planes example: `webgpu_clipping.html`
- ClippingGroup is available for WebGPU renderer but has bugs (GitHub issue #31779) — vertex colors with clipping cause incorrect rotation behavior
- Clipping planes work in both WebGL and WebGPU renderers

### WebGPU Renderer Maturity (Feb 2026 forum consensus)
- **WebGL is still the safe choice** for production apps in 2026
- WebGPU gaps: missing features/helpers, postprocessing not at full parity, materials behave differently
- Browser support improving but not universal (Safari recently added support)
- R3F + WebGPU works but has more friction than vanilla Three.js + WebGPU

### SOMA Architecture Recommendation
- **Keep WebGL2 as primary renderer** — reliable, mobile-compatible, full ecosystem
- **WebGPU as progressive enhancement** — detect support, offer as opt-in
- For cross-section rendering: use clipping planes with WebGL2 `renderer.clippingPlanes` (stable)
- The `ClippingGroup` pattern is the forward-looking approach but needs bug monitoring
- Dual-renderer strategy (ship WebGL, experiment WebGPU in parallel) is industry standard

### Technical Notes for Cross-Sections
- In Three.js, clipping planes are set on material (`material.clippingPlanes = [...]`)
- WebGPU renderer uses `ClippingGroup` instead of renderer-level clipping
- For anatomy cross-sections: define 1-2 planes (axial, sagittal), apply to mesh group
- Stencil buffer techniques can show interior colors at clip boundary


## Sources

- https://threejs.org/examples/webgpu_clipping.html
- https://discourse.threejs.org/t/webgpu-renderer-vanilla-three-js-vs-r3f-maturity-and-pitfalls/89661
- https://github.com/mrdoob/three.js/issues/31779
