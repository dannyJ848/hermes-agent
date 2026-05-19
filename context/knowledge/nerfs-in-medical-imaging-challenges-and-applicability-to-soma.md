# NeRFs-in-medical-imaging-challenges-and-applicability-to-SOMA

*Researched: 2026-04-05 15:19 CDT*

# Neural Radiance Fields in Medical Imaging: Challenges and Applicability to SOMA

**Source:** arXiv:2402.17797v2 (March 2024) — "Neural Radiance Fields in Medical Imaging: Challenges and Next Steps"

## Key Findings

### 4 Core Challenges for Medical NeRFs
1. **Fundamental imaging principles differ** — Medical images (CT, MRI, X-ray) use transmission/absorption physics, not reflectance. Standard NeRF volume rendering assumptions break.
2. **Inner structure requirement** — Organs are volumetric with internal heterogeneity, not opaque surfaces. NeRFs must model density gradients *inside* objects, not just at boundaries.
3. **Object boundary definition** — Soft tissue borders are ambiguous. No clear foreground/background separation like in natural scenes.
4. **Color density significance** — Medical grayscale values encode tissue properties (Hounsfield units), not appearance. Density values carry diagnostic meaning.

### Applicability to SOMA (Assessment)
- **Current SOMA approach (mesh-based Three.js/WebGL) is the correct choice** for real-time interactive anatomy education on mobile devices. Meshes provide: predictable performance, clear LOD control, easy labeling/annotation, and cross-platform compatibility.
- **NeRFs are complementary, not competitive** — Best suited for offline diagnostic reconstruction from sparse CT/MRI views, not real-time education rendering.
- **Future hybrid possibility:** A NeRF-processed CT scan could generate the base mesh that SOMA renders. NeRF as a pre-processing step, not runtime renderer.
- **3D Gaussian Splatting** (mentioned in 2025 literature) is emerging as a faster alternative to NeRFs that IS approaching real-time capability. Worth monitoring for future SOMA iterations.

### Datasets Mentioned
- Digitally Reconstructed Radiographs (DRR) as evaluation baseline
- Public medical NeRF datasets exist for organ-specific evaluation

### SOMA Architecture Decision
**Recommendation:** Continue mesh-based pipeline (DICOM → segmentation → mesh → glTF → Three.js). Monitor Gaussian Splatting maturity for potential future runtime renderer replacement. Do NOT pivot to NeRF runtime rendering — the 4 challenges above make it impractical for real-time mobile anatomy education today.


## Sources

- https://arxiv.org/html/2402.17797v2
- https://medium.com/@thekzgroupllc/3d-generative-models-and-neural-radiance-fields-nerfs-in-2025-570614792180
