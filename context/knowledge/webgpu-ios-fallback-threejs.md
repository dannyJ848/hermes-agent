# webgpu-ios-fallback-threejs

*Researched: 2026-04-05 16:16 CDT*

# WebGPU iOS Fallback Strategy for Three.js (2026)

## Key Finding
Three.js r171+ provides **automatic WebGPU → WebGL2 fallback** via the unified import:
```js
import * as THREE from 'three/webgpu'
```
This means you can ship WebGPU today without breaking older browsers. When WebGPU isn't available, it falls back to WebGL2 seamlessly.

## Browser Support (Jan 2026)
- Chrome/Edge v113+: Full support
- Firefox v141+ (Windows), v145+ (macOS)
- Safari v26+ (Sept 2025): macOS, iOS, iPadOS, visionOS
- **Global coverage: ~95%**

## iOS-Specific Status
- Safari on iOS supports WebGPU since iOS 26 (ships Sept 2025)
- For iOS < 17/26: automatic WebGL2 fallback via Three.js
- PlayCanvas reports WebGPU rendering black on iOS Safari if not configured — need WebGL2.0 as explicit fallback

## Decision Matrix for SOMA
- SOMA targets iOS via WKWebView → Three.js unified renderer handles fallback
- Custom shaders need conversion to TSL (Three Shader Language) which compiles to both WGSL and GLSL
- Compute shaders (GPU particle systems, volume rendering) only work on WebGPU — need feature detection to disable on WebGL2
- TSL syntax is the abstraction layer: write once, compiles to WGSL (WebGPU) or GLSL (WebGL2)

## Migration Steps
1. Update Three.js to r171+
2. Swap renderer import to `three/webgpu`
3. Handle async initialization (WebGPU renderer init is async, unlike WebGL)
4. Convert custom GLSL shaders to TSL
5. Implement feature detection for compute shader paths
6. Progressive enhancement: WebGL2 baseline, WebGPU adds compute effects

## Performance Note
WebGPU should outperform or match WebGL, but early benchmarks show cases where WebGPU is slower on mobile — need device-specific profiling. Compute shaders offer 10-100x gains for particle/physics workloads.

## SOMA Architecture Implication
Use TSL for all custom shaders in SOMA's subsurface scattering and anatomy layer compositing. Feature-detect WebGPU availability, and on WebGL2 fallback, disable GPU compute paths and use simplified rendering.


## Sources

- https://www.utsubo.com/blog/webgpu-threejs-migration-guide
- https://discourse.threejs.org/t/webgpu-renderer-vanilla-three-js-vs-r3f-maturity-and-pitfalls/89661
- https://forum.playcanvas.com/t/webgpu-fails-on-ios-safari/42070
