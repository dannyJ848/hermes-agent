# vision-grounding-gui-agents-2025

*Researched: 2026-04-07 04:52 CDT*

# Visual Grounding for GUI Agents: 2025 Advances

## GUI-Actor (Microsoft Research)
- **Coordinate-free visual grounding** — avoids the problems of coordinate generation approaches
- Key limitations of coordinate-based methods: weak spatial-semantic alignment, ambiguous supervision targets, mismatched feature granularity
- GUI-Actor proposes an alternative that doesn't rely on absolute coordinate prediction
- Relevant to SOMA: If we need agents to interact with 3D anatomy UIs, coordinate-free grounding could be more robust than bounding box prediction

## MINDCUBE (ICCV 2025 — Northwestern/Stanford/NYU/UW)
- **Spatial mental modeling from limited viewpoints** — tests if VLMs can reason about occluded spaces
- 21,154 questions across 3,268 images
- Tests 3 capabilities: cognitive mapping, perspective-taking, mental simulation
- SOTA VLMs barely beat random guessing on spatial reasoning
- "Map-then-reason" approach: 37.8% → 60.8% (SFT) → 70.7% (+RL)
- **Relevance to SOMA**: 3D anatomy viewers face the same challenge — users see one slice/angle and need to reason about occluded structures. The map-then-reason pattern (generate intermediate spatial representation → reason over it) maps directly to SOMA's cross-section and dissection features.

## Self-Evolutionary Visual Grounding (NeurIPS 2025)
- Enhancing visual grounding for GUI agents via self-evolutionary training
- References GUI-r1: R1-style vision-language action model for GUI agents
- Trend: RL-based training (GRPO-style) being applied to visual grounding tasks

## Key Takeaways for SOMA
1. Coordinate-free grounding > coordinate prediction for UI interaction
2. Map-then-reason pattern: build intermediate spatial repr before reasoning
3. RL fine-tuning dramatically improves spatial reasoning (37% → 70%)
4. VLMs are still weak at spatial reasoning about occluded objects — this is a frontier


## Sources

- https://www.microsoft.com/en-us/research/project/gui-actor-coordinate-free-visual-grounding-for-gui-agents/
- https://voxel51.com/blog/iccv-papers-vision-language-models
- https://neurips.cc/virtual/2025/poster/118788
