# draco-compression-glb-anatomy-pipeline

*Researched: 2026-04-05 12:55 CDT*

# Draco Compression for GLB Anatomy Models — SOMA Asset Pipeline

## Key Findings

### Compression Results
- **Draco geometry compression**: 90%+ reduction in mesh data (vertex positions, normals, UVs)
- **Texture compression (WebP)**: 50-70% smaller than JPEG/PNG; textures are typically 80% of file size
- **AVIF**: Even better than WebP for textures
- **Combined Draco + WebP**: Standard optimization pipeline for web GLB delivery

### Tool: gltf-transform CLI
```bash
npm install -g @gltf-transform/cli
# Full optimization pipeline:
gltf-transform optimize input.glb output.glb \
  --compress draco \
  --texture-compress webp \
  --texture-resize 1024
```

### Performance Targets (mobile)
- File size: <2MB per model for mobile
- FPS: 60 on mid-range devices
- Load time: <3s first render
- Unoptimized models increase load times by 300-500%

### SOMA Application
For SOMA's anatomy models (organs, tissues, skeletal system):
1. **Asset pipeline**: Run Draco compression during offline build, not at runtime
2. **LOD integration**: Create 3 Draco-compressed levels (high/med/low) at build time
3. **Texture strategy**: WebP for diffuse, consider KTX2/Basis for GPU-native compression on mobile
4. **Loading**: Use `DRACOLoader` with Three.js GLTFLoader — set decoder path to CDN or bundle WASM decoder
5. **Anatomy-specific**: Organs with subsurface scattering need higher-poly LODs close-up; Draco at lower LODs is ideal

### Three.js Integration
```javascript
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(dracoLoader);
```

### Mobile Safari Considerations
- WASM Draco decoder works in Safari but is slower than desktop
- Consider pre-decoding to standard GLB for iOS if load time exceeds 3s
- KTX2 textures (GPU-native) may be better than WebP for iOS GPU upload performance


## Sources

- https://www.axl-devhub.me/en/blog/optimizing-3d-models
- https://threejs.org/examples/jsm/libs/draco/
