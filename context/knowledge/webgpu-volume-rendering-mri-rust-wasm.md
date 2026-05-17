# WebGPU-Volume-Rendering-MRI-Rust-WASM

*Researched: 2026-04-12 19:02 CDT*

# Web MRI Volume Renderer in Rust (WASM + WebGL)

**Source:** armeet.ca/blog/2025/web-mri-volume-renderer-in-rust (Dec 2025)
**Author:** Armeet Singh Jatyani
**Repo:** github.com/armeetsinghjatyanii/web-mri-volume-renderer

## Architecture
- **Client:** Rust → WASM via trunk, egui/eframe for UI, glow for OpenGL shaders
- **Server:** axum (Rust), serves HDF5 volumes from disk
- **Rendering:** Ray marching via WebGL (initially tried WebGPU but had compatibility issues)

## Key Features
- Volume rendering in browser (WebGL ray marching)
- Trackball rotation (quaternion-based, no gimbal lock)
- Quality slider (adjust step size for performance/quality tradeoff)
- Opacity control
- Hover info card (voxel coordinates, value, intensity)
- Occupancy grid optimization (skip empty regions)
- XYZ axes visualization

## Performance Notes
- Handles 512³ MRI volumes (~8GB raw)
- Client-server architecture allows future expansion (chunking, database loading)
- Initially tried WebGPU but hit compatibility issues — fell back to OpenGL/WebGL

## Relevance to SOMA
- **Architecture pattern:** Rust→WASM for compute-heavy medical rendering is viable
- **Occupancy grid optimization:** Skip empty regions during ray marching — applicable to SOMA's anatomy rendering
- **WebGPU compatibility:** As of Dec 2025, WebGPU still has issues in some browsers; WebGL remains safer fallback
- **HDF5 support:** Standard medical imaging format; SOMA may need to support it
- **Quality slider:** Performance/quality tradeoff UI pattern useful for mobile


## Sources

- https://armeet.ca/blog/2025/web-mri-volume-renderer-in-rust
