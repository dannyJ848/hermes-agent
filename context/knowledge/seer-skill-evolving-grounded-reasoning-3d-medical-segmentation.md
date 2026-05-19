# SEER-Skill-Evolving-Grounded-Reasoning-3D-Medical-Segmentation

*Researched: 2026-04-07 15:57 CDT*

# SEER: Skill-Evolving Grounded Reasoning for Free-Text 3D Medical Image Segmentation

**Source:** arxiv:2603.08215v1, March 2026, Fudan University + USTC

## Key Innovation
SEER bridges linguistic variability and anatomical precision for free-text promptable 3D medical image segmentation through reasoning-driven design.

## Three Components
1. **SEER-Trace Dataset** — Pairs raw clinical requests with image-grounded, skill-tagged reasoning traces (reproducible benchmark)
2. **Grounded Reasoning Chain** — Constructs evidence-aligned target representation via vision-language reasoning chain that verifies clinical intent against image-derived anatomical evidence BEFORE voxel-level decoding
3. **SEER-Loop (Dynamic Skill-Evolving Strategy)** — Distills high-reward reasoning trajectories into reusable skill artifacts, progressively integrating them into subsequent inference → structured self-refinement

## Key Results
- Under linguistic perturbations: **81.94% reduction in performance variance**
- **18.60% improvement in worst-case Dice score**
- Robustness to abbreviations, synonyms, institution-specific conventions

## SOMA Relevance
- **Skill-evolving pattern** directly maps to our distillation pipeline — distilling reasoning traces into reusable artifacts
- **Vision-language reasoning chain** before decoding is exactly what SOMA needs for cross-section/dissection queries
- **Free-text promptable** paradigm = natural language anatomy exploration interface
- SEER-Loop concept could be applied to our medical terminology mapper (soma-bilingual-medical-terms skill)


## Sources

- https://arxiv.org/html/2603.08215
