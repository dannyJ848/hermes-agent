# visual-grounding-to-soma-3d-anatomy-synthesis

*Researched: 2026-04-07 11:53 CDT*

# Cross-Domain Synthesis: Visual Grounding → SOMA 3D Anatomy Interaction

## The Connection

GUI visual grounding techniques (bounding box detection, click target modeling, attention suppression) transfer directly to 3D anatomy interaction challenges in SOMA. This synthesis maps proven 2D grounding techniques to 3D medical visualization.

## Mapping Table

| GUI Visual Grounding Technique | SOMA 3D Anatomy Application |
|---|---|
| Bounding box prediction for UI elements | Raycasting hit-box generation for anatomical structures |
| Click target modeling (clickable area prediction) | Mesh picking zones — predict which anatomical region user intends to select |
| Attention suppression (ignore irrelevant UI elements) | Suppress occluded anatomy surfaces — don't select bones behind muscles |
| Multi-scale grounding (icon → button → panel) | Hierarchical anatomy selection (muscle fiber → muscle → muscle group → body system) |
| Visual context for disambiguation | Use camera angle + zoom level to disambiguate overlapping structures |
| Error recovery from visual feedback | Detect failed raycasts and suggest nearest valid anatomical target |

## ViewSRD Multi-View Decomposition → SOMA

The ICCV 2025 ViewSRD paper decomposes 3D grounding into structured multi-view reasoning. Applied to SOMA:

1. **Frontal view**: User's default camera angle — ground to surface anatomy
2. **Cross-section view**: Clip plane active — ground to internal structures
3. **Layer view**: Tissue layers toggled — ground to specific depth

Each view has different grounding strategies. Frontal uses surface normals; cross-section uses depth ranking; layered uses visibility masks.

## Implementation Path for SOMA

1. **Phase 1**: Three.js `Raycaster` with per-mesh metadata (already available via GLB userData)
2. **Phase 2**: Multi-hit disambiguation using camera-relative depth sorting
3. **Phase 3**: Hierarchical selection — click on rectus abdominis → offer to select "anterior abdominal wall" group
4. **Phase 4**: Visual feedback on hover — glow/highlight predicted target before click (reduces errors)
5. **Phase 5**: Natural language grounding — "select the heart" → camera + raycast to cardiac mesh

## Key Insight

The attention suppression technique from GUI agents is the most valuable transfer. In dense anatomy models, raycasting returns 5-15 hit points. The agent needs to suppress hits on:
- Occluded meshes (behind the front-facing surface)
- Disabled/toggled-off layers
- Non-interactive decorative meshes (connective tissue labels, etc.)

This is exactly the "ignore non-clickable elements" problem solved in GUI grounding.


## Sources

- https://openaccess.thecvf.com/content/ICCV2025/papers/Huang_ViewSRD_3D_Visual_Grounding_via_Structured_Multi_View_Decomposition_ICCV_2025_paper.pdf
- https://github.com/liudaizong/Awesome-3D-Visual-Grounding
- internal://visual-grounding-3d-medical skill
