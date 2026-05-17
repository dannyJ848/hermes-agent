# webgpu-webgl-frameworks-landscape-2026

*Researched: 2026-04-06 05:29 CDT*

# WebGPU/WebGL Frameworks Landscape (2026)

## Key Finding
Curated list of WebGL and WebGPU frameworks reveals ecosystem maturity. Most relevant for medical 3D rendering (SOMA project):

### Pure WebGPU Engines
- **Orillusion**: Pure Web3D rendering engine fully based on WebGPU standard
- **SWGPU**: Complete WebGPU implementation

### Best for Medical Visualization (WebGL/WebGPU hybrid)
- **Three.js**: Industry standard, vast ecosystem, WebGPU adapter in progress
- **Babylon.js**: Complete framework with volume rendering plugins
- **Filament**: PBR engine for Android/iOS/WASM — good for mobile SOMA

### Volume Rendering Specific
- **gi-voxels**: WebGL Voxel Cone Tracing — could enable real-time volume rendering
- **QuickVol** (from iScience 2024): Lightweight browser tool for immersive volumetric data viz, built on WebGL

### Key Insight for SOMA
Three.js remains the safest bet with its upcoming WebGPU backend (WebGPURenderer). For volume rendering of medical scans (CT/MRI), voxel cone tracing (gi-voxels pattern) combined with WebGPU compute shaders could achieve real-time performance on mobile. The WebGPU WGSL shader spec is actively developed (gpuweb/gpuweb repo).

### Action Items
1. Monitor Three.js WebGPU renderer maturity for SOMA migration
2. Investigate voxel cone tracing for anatomy cross-section rendering
3. Evaluate Orillusion for potential lighter-weight WebGPU-only build

## Sources

- https://gist.github.com/nixjs/668bbe31059610577e5dd46511b1d867
- https://www.cell.com/iscience/fulltext/S2589-0042(24)02604-X
- https://www.mdpi.com/2076-3417/15/5/2782
