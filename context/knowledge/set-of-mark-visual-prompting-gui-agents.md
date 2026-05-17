# set-of-mark-visual-prompting-gui-agents

*Researched: 2026-04-05 03:13 CDT*

# Set-of-Mark (SoM) Visual Prompting for GUI Agents

## What
**Set-of-Mark (SoM)** (arXiv:2310.11441, Microsoft Research, Oct 2023) is a visual prompting method that overlays alphanumeric marks, masks, and bounding boxes on segmented image regions to enhance visual grounding in Large Multimodal Models (LMMs) like GPT-4V.

## Key Mechanism
1. Use off-the-shelf segmentation models (SEEM/SAM) to partition an image into regions at multiple granularities
2. Overlay each region with a mark (number, letter, colored mask, or box)
3. Feed the marked image to an LMM, which can now reference specific regions by their marks
4. LMM answers questions requiring fine-grained visual grounding using the marks as anchors

## Results
- GPT-4V + SoM in **zero-shot** outperforms fully fine-tuned SOTA on RefCOCOg (referring expression comprehension)
- Works across a wide range of fine-grained vision and multimodal tasks
- No training required — purely a prompting/inference-time technique

## Relevance to GUI Agents
SoM is foundational for screen understanding in autonomous agents:
- **Screen element identification**: Segment UI elements (buttons, menus, text fields) and mark them for the LMM to reference
- **Action grounding**: Agent can specify "click on element [5]" instead of guessing coordinates
- **Multi-turn navigation**: Marked screens give the LLM persistent references across conversation turns
- **Combines with SAM**: Can use SAM to auto-segment any screen at runtime, then mark each region

## Related Work
- **UIPro** (ICCV 2025, Li et al.): 20.6M task samples for GUI grounding capability across platforms
- **Screen Stream Understanding** (EMNLP 2025): History screen awareness for mobile GUI agents (not just current observation)
- **Visual Prompt Encoder** (ICLR 2025): Trainable module that encodes visual prompt tokens alongside image and text tokens

## SOMA Integration Potential
- Could apply SoM to the SOMA 3D anatomy viewer — segment anatomical structures and mark them for LMM-based medical QA
- Browser automation: SoM-based grounding for Evey's browser tools (browser_vision, browser_click) could improve reliability vs. accessibility-tree-only navigation
- Medical image annotation: Use SAM + SoM to let LMMs answer questions about specific regions of DICOM/medical images


## Sources

- https://arxiv.org/abs/2310.11441
- https://aclanthology.org/2025.emnlp-main.920.pdf
- https://openaccess.thecvf.com/content/ICCV2025/papers/Li_UIPro_Unleashing_Superior_Interaction_Capability_For_GUI_Agents_ICCV_2025_paper.pdf
