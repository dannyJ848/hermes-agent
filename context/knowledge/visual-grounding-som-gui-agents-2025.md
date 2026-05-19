# visual-grounding-som-gui-agents-2025

*Researched: 2026-04-05 02:49 CDT*

# Visual Grounding for GUI Agents: SoM, RegionFocus, and CVPR 2025 Advances

## Set-of-Mark (SoM) Prompting
**Paper:** arXiv:2310.11441 (Yang et al., Microsoft, Oct 2023)
**Key idea:** Use interactive segmentation models (SEEM/SAM) to partition images into regions at multiple granularity levels, then overlay marks (alphanumerics, masks, boxes). Feed marked image to LMM (GPT-4V) for visual grounding.
**Result:** Zero-shot GPT-4V + SoM outperforms fully fine-tuned SOTA on RefCOCog referring expression comprehension.
**Relevance to SOMA:** SoM could enhance anatomy viewer interactions — segment anatomical structures with marks, then use LLM to answer spatial queries about them.

## RegionFocus: Visual Test-time Scaling for GUI Agent Grounding
**Paper:** ICCV 2025 (Luo, Logeswaran, Johnson, Lee)
**Key idea:** Progressive visual zoom approach for GUI grounding. Rather than processing entire screenshot at once, iteratively focus on regions of interest, scaling compute at test time for harder grounding tasks.
**Implication:** Test-time compute scaling applied to visual grounding — more iterations = better accuracy on complex screens.

## CVPR 2025 Visual Agent Landscape (Voxel51 Survey)
Five key papers forming the current frontier:
1. **From Multimodal LLMs to Generalist Embodied Agents** — Survey of methods for going from VLMs to agents that act
2. **ShowUI** — Vision-Language-Action model for GUI interactions
3. **GUI-Xplore** — Generalizable GUI agents via exploration-based training
4. **SpiritSight Agent** — GUI agent with Universal Block Parsing (previously researched)
5. **ComfyBench** — Benchmarking LLM agents in ComfyUI for collaborative AI systems

## Key Technical Trends
- **Interleaved vision-language-action sequences** — models must handle mixed modality streams
- **High-resolution screenshot processing** without losing detail (critical for dense medical UIs)
- **Precise element grounding** for reliable interaction (bounding boxes → coordinate actions)
- **Cross-platform compatibility** (web → mobile → desktop)
- **Interaction history management** across multiple observation-action cycles

## Application to Medical/SOMA Context
- SoM + medical image segmentation could enable natural language queries about anatomy
- RegionFocus-style progressive zoom maps well to hierarchical anatomy exploration
- GUI agent techniques apply to medical software automation (FHIR clients, PACS viewers)


## Sources

- https://arxiv.org/abs/2310.11441
- https://voxel51.com/blog/visual-agents-at-cvpr-2025
- https://openaccess.thecvf.com/content/ICCV2025/papers/Luo_Visual_Test-time_Scaling_for_GUI_Agent_Grounding_ICCV_2025_paper.pdf
