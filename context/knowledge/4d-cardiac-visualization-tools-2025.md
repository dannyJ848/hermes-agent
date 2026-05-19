# 4d-cardiac-visualization-tools-2025

*Researched: 2026-04-05 13:52 CDT*

# 4D Cardiac Image Workflow Tools (Hao et al., 2025)

**Source:** "Streamlining 4D Cardiac Image Workflows: Open-Source Tools for Segmentation, Registration, and Visualization" — PMC12885243, University of Pennsylvania.

## Key Tools

### 1. ITK-SNAP 4
- Natively 4D-optimized medical image tool
- Supports 4D image I/O, visualization, and segmentation
- Broad file type support for common 4D cardiac image formats

### 2. Greedy Propagation
- Intra-series registration tool
- Creates 4D segmentation from sparse 3D segmentations
- Reduces manual segmentation effort across time frames

### 3. Scherzo (most relevant to SOMA)
- **Fast web-based 4D model generation and visualization**
- Open-source
- Generates 3D/4D models from medical image data
- Could inform SOMA's web-based anatomy rendering approach

## SOMA Relevance
- Scherzo demonstrates that web-based 4D medical visualization is production-ready
- ITK-SNAP 4's 4D segmentation workflow could inspire SOMA's interactive dissection features
- Greedy Propagation's approach to propagating segmentations across frames could apply to SOMA's cross-section animation

## Citation
Hao, J., Yushkevich, P.A., et al. (2025). "Streamlining 4D Cardiac Image Workflows." Functional Imaging and Modeling of the Heart, 15673:161-173. DOI: 10.1007/978-3-031-94562-5_15

## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12885243/
