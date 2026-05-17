# set-of-mark-som-visual-grounding-gui-agents

*Researched: 2026-04-05 02:31 CDT*

# Set-of-Mark (SoM) Visual Grounding for GUI Agents

## Core Concept
Set-of-Mark (SoM) is a visual prompting method (Microsoft Research, 2023) that overlays numbered/lettered marks on image regions to dramatically improve visual grounding in Large Multimodal Models (LMMs) like GPT-4V. Instead of asking an LMM "click the submit button", you overlay numbered bounding boxes on all interactive elements and ask "click element #7".

**Paper:** arXiv:2310.11441 — "Set-of-Mark Prompting Unleashes Extraordinary Visual Grounding in GPT-4V"
**Repo:** github.com/microsoft/SoM (1.5k stars)
**Authors:** Jianwei Yang, Hao Zhang, Feng Li, Xueyan Zou, Chunyuan Li, Jianfeng Gao (Microsoft Research)

## SoM ToolBox Pipeline
1. **Segmentation:** Use SAM (Segment Anything Model) or detection model to identify regions
2. **Marking:** Overlay spatial marks (numbers, letters) on each segmented region
3. **Prompting:** Feed marked image + text prompt to LMM
4. **Grounding:** LMM references marks (e.g., "element #3") instead of ambiguous spatial descriptions

## Key Architecture Patterns

### OmniParser (Microsoft, 2024) — Production SoM for GUI Agents
The most complete implementation of SoM for screen understanding:
- **Icon Detection:** Fine-tuned YOLOv8-nano on 67K UI screenshots with DOM-derived bounding boxes
- **Text Extraction:** PaddleOCR for text regions
- **Icon Description:** Fine-tuned Florence-2 model generates semantic descriptions per detected element
- **Box Merging:** Adaptive algorithm removes redundant overlapping boxes
- **Output:** Structured DOM-like representation with numbered bounding boxes + functional descriptions

**Pipeline:** Screenshot → YOLO detection → OCR text extraction → Florence-2 description → Box merging → Marked image + structured data → GPT-4V action prediction

### UGround / SeeClick — Universal Visual Grounding for GUI Agents
- Advocates pure pixel-level visual grounding without HTML/DOM metadata
- SeeClick trains specialized grounding model on GUI screenshots
- UGround (arXiv:2410.05243) uses SoM-style marking for universal cross-platform grounding

## Key Technical Insights

1. **SoM reduces hallucination:** By anchoring LMM responses to numbered marks, spatial ambiguity is eliminated. GPT-4V accuracy on grounding tasks jumps significantly.

2. **Detection model matters more than LMM:** The quality of the initial segmentation/detection directly controls grounding accuracy. YOLOv8-nano fine-tuned on UI data outperforms generic detection.

3. **Local semantics bridge the gap:** Florence-2 descriptions attached to each bounding box help the LMM distinguish visually similar elements (e.g., two "Submit" buttons with different contexts).

4. **No DOM dependency:** SoM works on raw pixels — no accessibility tree, HTML, or view hierarchy needed. Critical for cross-platform (web, desktop, mobile) agents.

5. **Bilingual potential:** Since marks are language-agnostic numbers, the grounding layer is inherently language-independent. Text extraction (OCR) handles the language-specific part separately.

## Relevance to SOMA / Hermes Agent

### For Hermes browser tools (browser_vision, browser_snapshot):
- Current approach: accessibility tree text snapshot → element ref IDs
- SoM enhancement: overlay numbered marks on screenshot → ask VLM "which element is the login button?"
- Could improve accuracy on complex/dynamic pages where accessibility tree is incomplete

### For SOMA 3D anatomy viewer:
- SoM could enable interactive annotation: segment anatomy regions → overlay marks → ask VLM "what is structure #5?"
- Useful for the label collision avoidance problem researched in cycle 15

### For mobile GUI navigation:
- OmniParser's pipeline (YOLO detection + Florence-2 description) could be adapted for iOS accessibility testing
- YOLOv8-nano is mobile-friendly (~3M params)

## Implementation Resources
- **Microsoft SoM repo:** github.com/microsoft/SoM (includes demo notebooks)
- **OmniParser:** github.com/microsoft/OmniParser (production pipeline)
- **SAM integration:** SoM uses SAM for automatic segmentation when detection model unavailable
- **PaddleOCR:** Best OCR for multilingual text extraction (EN/ES support)


## Sources

- https://arxiv.org/abs/2310.11441
- https://github.com/microsoft/SoM
- https://som-gpt4v.github.io/
- https://learnopencv.com/omniparser-vision-based-gui-agent/
- https://arxiv.org/html/2410.05243v3
