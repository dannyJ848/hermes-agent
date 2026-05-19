# webgpu-2026-threejs-landscape

*Researched: 2026-04-06 20:19 CDT*

# WebGPU + Three.js Landscape (March 2026)

## Key Findings

### Universal Browser Support (Late 2025)
- WebGPU now has universal browser support across Chrome, Firefox, Safari, Edge
- Three.js r171+ includes WebGPURenderer with WebGL fallback

### Performance Gains
- **100x performance improvement** for LiDAR point clouds and millions of particles
- Compute shaders now available for collision detection and real-time filtering
- Reduced memory overhead and enhanced instancing for large models

### Three.js WebGPU vs Native WebGPU

| Feature | Three.js WebGPU | Native WebGPU |
|---------|----------------|---------------|
| Ease of Use | High | Low |
| Best For | Models <500MB, prototyping | Large models >500MB, simulations |
| Shader Dev | TSL simplifies shaders | Full control, requires expertise |
| Performance | Moderate for large datasets | High for massive datasets |

### Relevance to SOMA
- Three.js WebGPURenderer is practical for anatomy models (typically <500MB)
- Compute shaders could accelerate SSS, culling, and real-time filtering
- TSL (Three Shading Language) simplifies custom shader development
- WebGPU fallback to WebGL ensures iOS/Safari compatibility
- **Recommendation**: Migrate SOMA to Three.js r171+ WebGPURenderer when ready, keeping WebGL as fallback for older devices

### SIGGRAPH 2025 Real-Time SSS
- A SIGGRAPH 2025 Advances course on real-time subsurface scattering was published
- Covers skin rendering with closer ground truth matching
- PDF available at: https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
- **Next step**: Extract key techniques from this paper for SOMA's SSS shader implementation


## Sources

- https://altersquare.io/three-js-vs-webgpu-2026-large-scale-construction-viewers/
- https://advances.realtimerendering.com/s2025/content/sss-siggraph-2025-advances-published.pdf
