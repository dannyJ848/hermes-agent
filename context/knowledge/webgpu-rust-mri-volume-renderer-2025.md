# webgpu-rust-mri-volume-renderer-2025

*Researched: 2026-04-06 15:13 CDT*

# Web MRI Volume Renderer in Rust (2025)

**Source:** Armeet Singh Jatyani (Dec 2025) — github.com/armeetjatyani/web-mri-volume-renderer
**Demo:** Available online with 15s video walkthrough

## Key Technical Details

- **Architecture:** Client-server model. Rust client compiles to WASM via `trunk`, uses `egui`/`eframe` for UI, `glow` for WebGL rendering.
- **Rendering:** Ray marching volume rendering via OpenGL/WebGL shaders (NOT WebGPU — had compatibility issues).
- **Data format:** HDF5 (.h5) files on server, served via `axum` HTTP server.
- **Deployment:** Server on Fly.io, client as static WASM.
- **Performance:** Handles 512³ MRI volumes (~8GB raw samples from SKM-TEA 3D dataset).

## Features
- Volume rendering in browser (WebGL ray marching)
- Trackball rotation (quaternion-based, no gimbal lock)
- Quality slider (adjust step size for performance/quality tradeoff)
- Opacity control
- Hover info card (voxel coordinates, value, intensity)
- **Occupancy grid optimization** — skips empty regions (key perf optimization)
- XYZ axes visualization

## Relevance to SOMA

1. **Occupancy grid optimization** is directly applicable to SOMA's anatomy rendering — skip empty space in volumetric medical data.
2. **Quality slider with step size** is a good UX pattern for mobile vs desktop performance tradeoff.
3. **Ray marching over rasterization** for volume data — SOMA should consider this for CT/MRI integration.
4. **HDF5 format** — standard for medical imaging data. SOMA may need HDF5 parsing.
5. **Client-server architecture** — SOMA could offload heavy volumes to server, stream slices/chunks to client.
6. **WebGL fallback** — even though WebGPU is preferred, the author hit compatibility issues and fell back to WebGL. SOMA should plan for both.

## Performance Notes
- Browser achieved 67% of desktop performance for ray-casting 3D visualization (from DICOM article)
- At 24fps, volume rendering is "usable" in browser
- Occupancy grid is essential for interactive framerates

## Links
- Repo: github.com/armeetjatyani/web-mri-volume-renderer
- Demo website available
- Author: AI researcher, former 3D medical imaging work (knee/brain MRI)


## Sources

- https://armeet.ca/blog/2025/web-mri-volume-renderer-in-rust
