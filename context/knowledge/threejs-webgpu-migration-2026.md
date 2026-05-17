# threejs-webgpu-migration-2026

*Researched: 2026-04-06 18:49 CDT*

# Three.js WebGPU Migration Guide (2026)

## Key Finding
Three.js r171 (September 2025) introduced production-ready WebGPU renderer. Migration is often a one-line change: swap `WebGLRenderer` for `WebGPURenderer`.

## Browser Coverage (Jan 2026)
- Chrome/Edge v113+ (May 2023): Full support
- Firefox v141+ (Windows), v145+ (macOS): Enabled by default
- Safari v26+ (September 2025): macOS, iOS, iPadOS, visionOS
- **Global coverage: ~95%** with automatic WebGL 2 fallback for remaining 5%

## Migration Steps (from utsubo.com guide)
1. Audit current setup
2. Update Three.js to r171+
3. Swap renderer import: `WebGLRenderer` → `WebGPURenderer`
4. Handle async initialization (WebGPU init is async unlike WebGL)
5. Update post-processing
6. Convert custom shaders to TSL (Three Shader Language)
7. Implement fallback detection
8. Cross-browser testing

## TSL (Three Shader Language)
- Replaces raw WGSL/GLSL
- Compiles to both WGSL and GLSL automatically
- Future-proofs shader code

## Compute Shaders
- Unlock 10-100x performance gains for particle systems and physics
- Critical for medical volume rendering and tissue simulation

## React Three Fiber
- Supports WebGPU via `gl` prop factory pattern
- Drei compatibility needs verification per-component

## Decision Matrix for SOMA
- SOMA hits performance walls with complex anatomy models → **MIGRATE**
- Kiosk/installation with controlled hardware → **MIGRATE**
- Heavy custom GLSL shaders (SSS) → Evaluate TSL first

## SOMA Impact
SOMA should plan migration to WebGPU renderer:
1. Switch to Three.js r171+ (or latest)
2. Use WebGPURenderer with WebGL2 fallback
3. Convert SSS shaders to TSL for cross-backend compatibility
4. Leverage compute shaders for real-time tissue simulation
5. Safari iOS support via v26+ means mobile WebGPU is viable


## Sources

- https://www.utsubo.com/blog/webgpu-threejs-migration-guide
- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
