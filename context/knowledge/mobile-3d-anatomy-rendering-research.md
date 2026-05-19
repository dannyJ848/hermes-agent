# mobile-3d-anatomy-rendering-research

*Researched: 2026-04-02 00:14 CDT*

# Mobile 3D Anatomy Rendering Research (April 2026)

## Three.js Mobile Performance (100 Tips - Utsubo)
Source: utsubo.com/blog/threejs-best-practices-100-tips

Key rules for SOMA:
1. WebGPU renderer production-ready since r171 with zero-config + WebGL 2 fallback
2. Target <100 draw calls/frame
3. InstancedMesh for repeated objects (organs)
4. BatchedMesh for varied geometries
5. Dispose ALL GPU resources: geometries, materials, textures, render targets
6. mediump precision on mobile shaders
7. Object pooling for spawned entities
8. frameloop="demand" for static scenes
9. useFrame for mutations, never setState
10. three-mesh-bvh for fast raycasting
11. TSL (Three Shader Language) is the future - write once, run WebGPU/WebGL
12. Bake lightmaps for static scenes (anatomy doesn't animate)
13. Limit active lights to 3 or fewer
14. Use environment maps for ambient light (faster than real lights)
15. Lazy load 3D content, code-split Three.js modules

## On-Device AI Inference (Sub-20ms in 2026)
Source: alephzerolabs.com/blog/on-device-ai-2026-sub-20ms

Benchmarks on 2024-2025 mid-range phones ($400):
- Image classification (MobileNetV3): 4-8ms
- Object detection (YOLO variants): 12-20ms
- Pose estimation (MoveNet Thunder): 15-25ms
- Text recognition (CRNN OCR): 10-18ms
- ALL with INT8 quantization, NPU acceleration

Frameworks:
- ExecuTorch (Meta): PyTorch-native, delegates to CoreML/XNNPACK/QNN
- React Native ExecuTorch: Hooks-based RN integration
- LiteRT (TFLite rebranded): 1.4x faster cross-platform GPU perf
- CoreML 7: Apple Silicon optimized
- ONNX Runtime Edge: Cross-framework

Key insight: Privacy by architecture. Medical data never leaves device. No cloud needed for inference.

## Progressive 3D Loading (Needle Tools)
Source: engine.needle.tools/docs/gltf-progressive

@needle-tools/gltf-progressive:
- Single-line integration for any Three.js project
- Creates tiny initial file (300KB proxy) + LOD files that stream on demand
- 56MB asset → 300KB initial + up to 8MB progressive streaming
- Mesh LODs: up to 6 levels, each ~half triangles of previous
- Texture LODs: 128px preview embedded, full-res streams progressively
- Density-based selection (triangles per pixel, not just distance)
- Mobile: automatic quality reduction
- Supports KTX2, WebP, Draco, Meshopt compression
- Fast raycasting uses low-poly LOD meshes

npm: @needle-tools/gltf-progressive

## Mobile GPU Budgets
Source: PlayCanvas forum, MDN WebGL best practices

Mobile hard limits:
- Draw calls: 100-150 max (target 50-100)
- Triangle budget: 100K-200K on screen
- Texture memory: 100-200MB
- iOS WKWebView: ~350MB total memory limit
- Android WebView: ~512MB total memory limit
- iOS kills process silently when exceeding memory

Best practices:
- Batch draw calls into fewer, larger calls
- Use lower precision data types
- Minimize branching in shaders
- Atlas textures to reduce binds
- Merge static geometry
- Share materials between meshes

## Touch Gestures in R3F Native
Source: Lobehub touch-gesture-3d skill, Three.js discourse

Architecture:
1. react-native-gesture-handler captures raw touch
2. R3F Canvas receives pointer events
3. Three.js Raycaster determines hit object
4. onPointerDown handlers fire with e.stopPropagation() to prevent OrbitControls
5. Always use onPointerDown (not onClick) for faster mobile response

Key patterns:
- e.stopPropagation() is CRITICAL on every interactive mesh
- Use invisible placement planes for tap-to-place
- Gate OrbitControls during drag operations
- iOS and Android handle touch events differently

## Tauri 2.0 Mobile
Source: v2.tauri.app/concept/architecture

- iOS: WKWebView (Safari)
- Android: System WebView (Chromium)
- Rust backend compiles to native binary (hard to reverse engineer)
- IPC between WebView and Rust via message passing
- SQL plugin for SQLite
- Same Rust binary runs on desktop and mobile
- Uses system WebView (small app size, no Chromium bundled)


## Sources

- https://www.utsubo.com/blog/threejs-best-practices-100-tips
- https://alephzerolabs.com/blog/on-device-ai-2026-sub-20ms/
- https://engine.needle.tools/docs/gltf-progressive/
- https://v2.tauri.app/concept/architecture/
- https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices
