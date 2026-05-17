# set-of-mark-visual-grounding-ui-detection

*Researched: 2026-04-05 01:58 CDT*

# Set-of-Mark (SoM) Visual Grounding for UI Element Detection

## Overview
**Set-of-Mark (SoM)** is a visual prompting technique from Microsoft Research (Yang et al., 2023, arXiv:2310.11441) that dramatically improves visual grounding in Large Multimodal Models (LMMs) like GPT-4V.

## Core Method
1. Use an interactive segmentation model (SAM/SEEM) to partition an image into regions at different granularity levels
2. Overlay these regions with **marks** — alphanumerics, masks, bounding boxes
3. Feed the marked image to an LMM along with a question
4. The LMM can now **reference specific regions by mark ID** for precise visual grounding

## Key Results
- Zero-shot GPT-4V + SoM **outperforms** fully fine-tuned SOTA on RefCOCOg (referring expression comprehension)
- Applicable to: object detection, segmentation, visual QA, image captioning
- Code: github.com/microsoft/SoM (1.5k stars, MIT license)

## Relevance to Agent Vision (Evey/SOMA)

### For browser_vision / screen understanding:
- Current approach: browser_snapshot (accessibility tree) + browser_vision (screenshot analysis)
- **SoM enhancement**: Overlay numbered marks on screenshot → ask vision model to identify elements by number
- This bridges the gap between accessibility tree (text-based) and raw pixel understanding
- Particularly useful for: canvas/WebGL content, apps with poor accessibility trees, game UIs

### For Hermes agent specifically:
- `browser_vision` with `annotate: true` already implements a primitive form of SoM ([N] labels → @eN refs)
- Could be enhanced by using SAM for **automatic region detection** instead of relying on DOM elements
- YOLO5 (used in MP-GUI, CVPR 2025) is another option for detecting graphics/icons on screen

## Related Papers & Techniques

### MP-GUI (CVPR 2025)
- Uses enhanced YOLO5 to detect on-screen graphics
- Draws bounding boxes (SoM-style) for MLLM-based GUI understanding
- Combines modality perception (text + icon + image) for comprehensive UI understanding

### Enhancing VLMs for Mobile UI (ACL Findings 2025)
- Training VLMs on perception + reasoning tasks for mobile UI
- Perception: holistic understanding of UI design and components
- Reasoning: task completion, navigation planning

### Iterative Visual Prompting for Design Critique (OpenReview 2025)
- Iterative refinement approach: screenshot → critique → refined prompt
- Applicable to UI testing and automated QA

## Implementation Path for Hermes
1. **Phase 1**: Use existing `browser_vision annotate:true` for DOM-backed SoM
2. **Phase 2**: Add SAM-based segmentation for non-DOM content (canvas, images)
3. **Phase 3**: Combine accessibility tree + SoM marks for hybrid grounding
4. **Phase 4**: Use for automated UI testing (dogfood skill integration)

## Key Insight
The `annotate: true` parameter in `browser_vision` is already a basic SoM implementation. The next step is making it work for non-DOM content and improving mark quality with segmentation models.


## Sources

- https://arxiv.org/abs/2310.11441
- https://github.com/microsoft/SoM
- https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_MP-GUI_Modality_Perception_with_MLLMs_for_GUI_Understanding_CVPR_2025_paper.pdf
- https://aclanthology.org/2025.findings-acl.1295.pdf
