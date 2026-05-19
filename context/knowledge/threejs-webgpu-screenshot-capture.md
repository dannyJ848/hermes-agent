# threejs-webgpu-screenshot-capture

*Researched: 2026-04-05 02:10 CDT*

# Three.js WebGPU Screenshot/Framebuffer Capture

## Key Finding
WebGPU renderer in three.js has **fundamentally different** screenshot mechanics vs WebGL. The classic `preserveDrawingBuffer + toDataURL()` pattern does NOT work with WebGPU.

## WebGL Approach (works but has caveats)
- `preserveDrawingBuffer: true` on WebGLRenderer → `canvas.toDataURL()` 
- **Better approach**: Don't use preserveDrawingBuffer. Instead, call `renderer.render(scene, camera)` then immediately `canvas.toDataURL()` in the same frame. The buffer is valid until the next `clear()`.
- SO answer: "You don't need preserveDrawingBuffer to take screenshots. Re-render and capture in same frame."

## WebGPU Challenges
1. **`readRenderTargetPixelsAsync` returns blank** (Issue #31658, fixed in #31765 for r180+)
   - Must set RenderTarget on renderer BEFORE any render call
   - ColorSpace must be explicitly set (NoColorSpace or LinearSRGBColorSpace)
   - Animation loop captures need careful timing — read AFTER renderAsync completes
   
2. **`canvas.toDataURL()` with WebGPU** — Unity WebGPU devs report `preserveDrawingBuffer` does not exist for WebGPU canvas. Must use GPU-side readback instead.

3. **OffscreenCanvas + WebGPU** (Issue #33251) — Currently "won't fix" for inspector integration. WebGPU + OffscreenCanvas works but tooling support is limited.

## Recommended Approach for SOMA
For anatomy viewer screenshots (e.g., capturing current view for OCR or SoM annotation):
1. Use `WebGPURenderer.readRenderTargetPixelsAsync()` on a RenderTarget
2. Wrap in async pattern: `await renderer.renderAsync(scene, camera)` then `await renderer.readRenderTargetPixelsAsync(renderTarget)`
3. Convert pixel data to ImageData → canvas → toDataURL for downstream processing
4. Alternative: Use `WebGLRenderer` with fallback if WebGPU capture fails (SOMA already has WebGPU fallback to WebGL)

## Relevance to SoM Visual Grounding
For Set-of-Mark annotation on SOMA's 3D anatomy models:
- Capture frame → send to vision model with SoM markers
- Must handle WebGPU readback timing carefully
- Consider pre-rendering markers as overlay on 2D canvas (avoids GPU readback entirely)


## Sources

- https://github.com/mrdoob/three.js/issues/31658
- https://github.com/mrdoob/three.js/issues/33251
- https://stackoverflow.com/questions/30628064/how-to-toggle-preservedrawingbuffer-in-three-js
- https://discussions.unity.com/t/how-to-take-a-screenshot-with-unity-webgpu/1681498
