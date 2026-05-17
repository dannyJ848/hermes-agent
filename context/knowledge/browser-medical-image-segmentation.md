# browser-medical-image-segmentation

*Researched: 2026-04-02 18:03 CDT*

# Medical Image Segmentation in the Browser

## Key Finding: SAM + MedSAM Can Run In-Browser via ONNX Runtime Web

### Most Viable Path: @xenova/transformers.js + SAM
```javascript
import { SamModel, AutoProcessor, RawImage } from '@xenova/transformers';
const model = await SamModel.from_pretrained('Xenova/sam-vit-base');
```
- SAM ViT-B (91M params, ~350MB ONNX) runs on desktop Chrome/WebGPU: 1-4s encoder, 50-100ms decoder
- MobileSAM (~5M params, ~40MB ONNX): 200-500ms encoder on desktop, 2-8s on mobile
- **MedSAM** (fine-tuned on 1.5M medical masks, CT/MRI/X-ray) — same architecture, drop-in ONNX replacement

### Critical Repos
| Repo | Purpose |
|------|---------|
| `xenova/transformers.js` | Easiest SAM-in-browser path (npm install) |
| `ChaoningZhang/MobileSAM` | Lightweight SAM for mobile (~40MB) |
| `bowang-lab/MedSAM` | SAM fine-tuned on medical images |
| `cornerstonejs/cornerstone3D` | DICOM/NIfTI viewer with segmentation rendering (no ML) |
| `Kitware/vtk-js` | 3D medical viz (volume rendering, isosurface) |

### Mobile Reality Check
- WebGPU NOT available on iOS Safari or Chrome Android yet
- WebGL fallback: SAM ViT-B takes 15-60s on mobile (often OOM)
- **Strategy**: Server-side inference + browser rendering for mobile, or lightweight U-Net (~5M params)

### The Gap (Opportunity for SOMA)
No open-source project combines: medical image loading + ML segmentation in-browser + 3D rendering. This is exactly what SOMA could pioneer.

### Performance Table
| Model / Device | Desktop WebGPU | Mobile WebGL |
|----------------|---------------|-------------|
| SAM ViT-B encoder | 1-4s | 15-60s (OOM) |
| SAM ViT-B decoder | 50-100ms | 500ms-2s |
| MobileSAM encoder | 200-500ms | 2-8s |
| MobileSAM decoder | 30-50ms | 200-500ms |

### Integration Architecture for SOMA
1. Load pre-segmented anatomy masks as textures (no real-time segmentation needed for base app)
2. For "interactive exploration": use MobileSAM for click-to-segment on visible 3D surface
3. Segmentation mask → texture → Three.js mesh extraction (marching cubes)
4. Pre-compute common organ segmentations offline, serve as compressed GLB meshes


## Sources

- https://github.com/xenova/transformers.js
- https://github.com/bowang-lab/MedSAM
- https://github.com/ChaoningZhang/MobileSAM
- https://github.com/cornerstonejs/cornerstone3D
