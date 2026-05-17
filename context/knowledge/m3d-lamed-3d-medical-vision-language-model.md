# M3D-LaMed 3D Medical Vision-Language Model

*Researched: 2026-04-07 09:13 CDT*

# M3D-LaMed: Multi-Modal Large Language Model for 3D Medical Imaging

**Repo:** https://github.com/BAAI-DCAI/M3D
**Stars:** 428
**Language:** Python (PyTorch)
**Organization:** BAAI (Beijing Academy of AI)

## What It Does
M3D-LaMed is a pioneering multi-modal LLM specifically designed for 3D medical image analysis. It combines:
- **3D Vision Encoder** — extracts features from volumetric medical scans (CT, MRI)
- **3D Spatial Pooling Perceiver** — efficiently handles large 3D volumes
- **Language Model** — supports multiple medical tasks through natural language

**Supported Tasks:**
- 3D medical image segmentation
- Report generation from scans
- Visual question answering (VQA) about anatomy/pathology
- Grounding (identifying regions from text descriptions)

## Why It Matters for SOMA
- Could power **automated anatomy labeling** in SOMA's 3D models
- VQA capability could enable "ask about this organ" features
- Report generation could create medical content for SOMA's encyclopedia
- Grounding could map natural language to 3D anatomy coordinates

## Technical Architecture
- Built on PyTorch with custom 3D vision encoder
- Supports multiple LLM backends (Phi3, LLaMA)
- Trained on large-scale 3D medical datasets
- Zero-shot and few-shot capabilities

## Integration Path
1. Deploy as a backend service (Flask/FastAPI)
2. Expose via MCP server for Hermes agent integration
3. Use for batch annotation of SOMA's anatomy models
4. Power "Ask about this organ" feature in SOMA

## Related Work
- Med3DVLM (mirthAI/Med3DVLM) — more efficient variant
- MedicalNet (Tencent) — pretrained 3D backbones
- MONAI Model Zoo — production medical AI models


## Sources

- https://github.com/BAAI-DCAI/M3D
- https://openreview.net/forum?id=XQL4Pmf6m6
- https://arxiv.org/html/2503.20047v1
