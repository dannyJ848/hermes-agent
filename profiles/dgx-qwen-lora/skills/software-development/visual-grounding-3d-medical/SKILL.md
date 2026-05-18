---
name: visual-grounding-3d-medical
version: 1.0
description: Apply GUI visual grounding techniques to 3D medical anatomy UI. Maps natural language anatomy terms to 3D mesh coordinates, enabling voice-driven and bilingual anatomy exploration.
trigger: When implementing anatomy search, element picking, or natural-language-driven 3D navigation in SOMA.
tags: [soma, vision, webgpu, threejs, medical, grounding]
---

# Visual Grounding for 3D Medical Anatomy UI

## The Core Problem

GUI visual grounding: "Click the Submit button" → screen coordinates (x, y)
SOMA anatomy grounding: "Show me the temporal bone" → 3D mesh coordinates (x, y, z) + mesh ID

Both are **semantic-to-spatial mapping** — the same fundamental problem in different spaces.

## Research Foundation (2025-2026)

### Phi-Ground (Microsoft Research, Jan 2026)
- GUI grounding = agent's perception system translating instructions to screen coordinates
- Coordinate regression approach: language → bounding box center
- **Application to SOMA**: Train coordinate regression for anatomy term → mesh centroid

### Aria-UI (ACL 2025)
- Visual grounding for GUI instructions without HTML/AXTree reliance
- Pure visual grounding — no accessibility tree needed
- **Application to SOMA**: Ground anatomy terms from visual rendering, not just scene graph metadata

### Visual Test-time Scaling (ICCV 2025)
- Simple visual scaling at inference improves VLM-based grounding
- No retraining — just more compute at query time
- **Application to SOMA**: Spend more compute for ambiguous anatomy queries (e.g., "that bone near the ear")

### Screen Stream Understanding (EMNLP 2025)
- History screens provide crucial context for GUI agents
- Current-frame-only agents miss temporal patterns
- **Application to SOMA**: Cross-section navigation history = spatial context for grounding

### Self-Evolutionary Visual Grounding (NeurIPS 2025)
- Self-evolutionary training improves grounding across diverse platforms
- **Application to SOMA**: User interaction history improves anatomy grounding over time

## SOMA Feature: Anatomy Grounding API

```typescript
interface AnatomyGroundingResult {
  meshId: string;           // Three.js mesh UUID
  centroid: Vector3;        // World-space center of mesh
  boundingBox: Box3;        // For camera framing
  confidence: number;       // 0-1, from grounding model
  alternatives: {           // Ambiguous matches
    meshId: string;
    confidence: number;
  }[];
}

// Core function — maps language to 3D coordinates
function groundAnatomyTerm(
  term: string,                              // "temporal bone" or "hueso temporal"
  context: CrossSectionHistory[],            // Navigation history for spatial context
  scene: THREE.Scene                         // Current 3D scene with meshes
): AnatomyGroundingResult
```

### Implementation Phases

**Phase 1: Scene Graph Grounding (no ML needed)**
- Use existing anatomy hierarchy (ZAnatomyLoader data) as "accessibility tree"
- String matching against mesh names, Latin names, and bilingual terms
- Fuzzy matching via Levenshtein distance
- This alone covers 80% of use cases

**Phase 2: Visual Grounding with Embeddings**
- Embed anatomy descriptions with a small model
- Pre-compute embeddings for all mesh metadata at load time
- At query: embed user term → cosine similarity search → return top matches
- Handles synonyms, misspellings, bilingual queries

**Phase 3: Learned Coordinate Regression**
- Fine-tune a small model (Phi-Ground pattern) on anatomy term → mesh centroid
- Training data: mesh names + bounding box centers from Z-Anatomy
- Enables "the bone near the ear" style queries via spatial reasoning

**Phase 4: User Interaction History**
- Track which meshes users click/zoom after grounding queries
- Use as implicit feedback to improve grounding confidence
- Self-evolutionary pattern from NeurIPS 2025

## Bilingual Support

The grounding API should handle both English and Spanish anatomy terms:
- Use the bilingual terminology mapper (soma-bilingual-medical-terms skill)
- Embed both languages in the same vector space
- Query in either language returns the same mesh

## Camera Framing

After grounding, automatically frame the camera:
```typescript
function frameAnatomy(result: AnatomyGroundingResult, camera: THREE.Camera) {
  const target = result.centroid;
  const distance = result.boundingBox.getSize(new Vector3()).length() * 1.5;
  // Animate camera to target + distance
  animateCamera(camera, target, distance);
}
```

## Three.js Picking Implementation (for Phase 1)

The standard Three.js approach for 3D element selection:
1. **Raycaster** — cast ray from mouse/touch through camera frustum
2. Check bounding sphere/box intersection first (cheap), then triangles (expensive)
3. For 1000+ anatomy meshes: use `layers` or `userData.anatomyId` to filter raycast targets
4. **GPU picking** — render each mesh with unique color to offscreen buffer, read pixel at click point
5. For mobile: `touchstart` event → normalize coords → raycaster.intersectObjects()

Reference: https://threejs.org/manual/en/picking.html

## Latest Research (2025)

### VividMed: Versatile Visual Grounding for Medicine (NAACL 2025)
- Medical VLM supporting BOTH segmentation masks AND bounding boxes
- Handles 2D AND 3D imaging modalities (CT, MRI, X-ray)
- 3-stage training: grounding pre-training → medical instruction tuning → alignment
- **Key finding**: Visual grounding training IMPROVES VQA and report generation performance
- Architecture: Base VLM + Localization Module
- Code: https://github.com/function2-llx/MMMM
- **SOMA Application**: Localization module architecture directly adaptable for anatomy grounding. Grounding training dual-benefit means investing in grounding improves all SOMA capabilities.

### MedGround-R1 (MICCAI 2025)
- Spatial-aware bounding box prediction for medical images
- Superior bounding box alignment with ground truth vs prior methods
- **SOMA Application**: Spatial grounding precision techniques for anatomy label placement

### VolView + NVIDIA Clara (Kitware, Nov 2025)
- Browser-native medical imaging: WebGL/WebGPU + VTK.js + ITK-WASM
- Runs entirely client-side — zero installation, no backend servers
- Cinematic volume rendering, MPR, segmentation all in browser
- **SOMA Application**: Validates browser-native approach. ITK-WASM for DICOM/NIfTI parsing, VTK.js as potential Three.js complement for volume rendering.

## Sources
- Phi-Ground: https://www.microsoft.com/en-us/research/articles/phi-ground-improving-how-ai-agents-navigate-screen-interface/
- Aria-UI: https://aclanthology.org/2025.findings-acl.1152.pdf
- Visual Test-time Scaling: ICCV 2025
- Screen Stream Understanding: EMNLP 2025
- Self-Evolutionary Visual Grounding: NeurIPS 2025
- VividMed: https://arxiv.org/html/2410.12694v2
- MedGround-R1: MICCAI 2025 (papers.miccai.org)
- VolView+Clara: https://www.kitware.com/integrating-nvidia-clara-models-into-volview-a-technical-deep-dive/
- Cross-domain synthesis: ~/wiki/concepts/synthesis-visual-grounding-anatomy-ui.md
- Today's research: ~/wiki/concepts/vision-medical-grounding-2025.md
