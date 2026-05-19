# webgpu-mobile-support-verified-2026

*Researched: 2026-04-02 18:19 CDT*

# WebGPU Mobile Browser Support — Verified April 2026

## Critical Finding: iOS WebGPU requires iOS 26+

**Safari 26.0** ships WebGPU on macOS Tahoe 26, iOS 26, iPadOS 26, and visionOS 26.
Announced September 2025. This means:
- iOS 17, 18, 19, 20, 21, 22, 23, 24, 25 = NO WebGPU
- iOS 26+ = WebGPU available
- iPhone 14 running any iOS < 26 = WebGL2 only

## Desktop/Laptop Coverage (Nov 2025+)
- Chrome 113+ — all platforms since 2023
- Firefox 141+ — Windows, macOS (145+)
- Safari 26 — macOS Tahoe 26+
- Edge — via Chromium

## Android Coverage
- Chrome 121+ — Android 12+ with Qualcomm/ARM GPUs
- Firefox Android — in progress, expected 2026

## SOMA Implications
1. **Primary renderer MUST be WebGL2** — iOS 26 adoption will take years
2. **WebGPU is progressive enhancement** — use for compute/SSS on supporting devices
3. **TSL approach is correct** — Three.js TSL compiles to both WGSL and GLSL
4. **SSS via MeshSSSNodeMaterial** — works on both WebGPU and WebGL2 via TSL
5. **No rush to WebGPU renderer** — keep WebGL2 renderer, let node materials handle the dual path

## Deployment Target
- iPhone 14+ with iOS 17+ = WebGL2 (current target)
- iPhone 14+ with iOS 26+ = WebGPU when available (future enhancement)
- Chrome Android 121+ = WebGPU available now


## Sources

- https://www.webgpu.com/news/webgpu-hits-critical-mass-all-major-browsers/
- https://web.dev/blog/webgpu-supported-major-browsers
- https://developer.apple.com/documentation/safari-release-notes/safari-26-release-notes
