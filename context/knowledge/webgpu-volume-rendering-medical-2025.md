# webgpu-volume-rendering-medical-2025

*Researched: 2026-04-06 14:37 CDT*

# WebGPU Volume Rendering for Medical Imaging (2025-2026)

## Key Developments

### Chrome 139 Native Support
Chrome 139 added native **3D texture volume rendering** in WebGPU, including a sample showing 3D brain scans. This removes the need for 2D texture slice workarounds.
- Source: https://developer.chrome.com/blog/new-in-webgpu-139
- Feature: `texture_3d` in WGSL shaders for direct volume rendering

### Three.js MRI Raycast Engine
Community project: **WebGPU MRI Raycast Engine** — real-time brain reconstruction from MRI scans in the browser.
- **Performance**: ~100fps on Intel integrated graphics (Core i3)
- **Features**: Full tissue segmentation, 3D brain reconstruction
- **Framework**: Built on Three.js with WebGPU renderer
- Forum: https://discourse.threejs.org/t/webgpu-mri-raycast-engine-real-time-brain-reconstruction-in-the-browser/89988

### WebGPU 3D CT Visualization
Real-time 3D CT volume visualization running in Chrome browser.
- Reddit thread: https://www.reddit.com/r/webgpu/comments/1r0p2kw/realtime_3d_ct_volume_visualization_in_the_browser/
- Chrome-only for now

### Live Demo
Working WebGPU volume rendering demo (3D texture): https://feng3d.com/webgpu/src/webgpu/volumeRenderingTexture3D/index.html

### Academic Papers
- MDPI: WebGPU-based volume rendering framework for interactive scalar data visualization (https://www.mdpi.com/2076-3417/15/5/2782)
- ACM: FusionRender — 29.3%-122.1% improvement over existing baselines (https://dl.acm.org/doi/abs/10.1145/3589334.3645395)
- ResearchGate: WebGPU for privacy-preserving dermatological diagnostics (client-side AI)

## SOMA Implications
1. **Texture3D is now native in Chrome** — SOMA can use WGSL 3D textures for direct volume rendering of CT/MRI data without polyfill
2. **Three.js + WebGPU raycast engine** at 100fps on iGPU means SOMA's mobile target (A15/M1) should achieve similar or better performance
3. **Architecture path**: Replace current slice-based anatomy rendering with WebGPU compute ray-marching through 3D textures
4. **Mobile timeline**: WebGPU on Safari is still experimental — need WebGL2 fallback for iOS short-term


## Sources

- https://developer.chrome.com/blog/new-in-webgpu-139
- https://discourse.threejs.org/t/webgpu-mri-raycast-engine-real-time-brain-reconstruction-in-the-browser/89988
- https://www.mdpi.com/2076-3417/15/5/2782
- https://feng3d.com/webgpu/src/webgpu/volumeRenderingTexture3D/index.html
