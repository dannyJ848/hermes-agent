---
name: scientific-skills
description: Gateway to 134+ specialized scientific skills from scientific-agent-skills. Covers 17 high-level domains including Bioinformatics, Cheminformatics, Medical Imaging, Physics, Laboratory Automation, and more. Fetches expert reference material on demand.
version: 1.1.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [science, biology, chemistry, physics, engineering, research, bioinformatics, cheminformatics, medical, data-science, analytics, lab-automation]
    category: research
---

# Scientific Agent Skills Gateway (v1.1.0)

The **Scientific Agent Skills Gateway** serves as a centralized index and retrieval system for the `scientific-agent-skills` library. It provides access to over **134 specialized skills** across **17 high-level scientific domains**, ranging from bioinformatics to quantum computing.

## Core Functionality
Instead of bundling all skills locally, this gateway indexes domain-specific expert patterns, references, and executable scripts to be fetched on demand.

> **Usage Scenario:** Use when asked about molecular analysis, drug discovery, genomic/transcriptomic data processing, physics simulations, astronomical calculations, professional scientific writing, grant preparation, clinical reports, or any high-level scientific research task.

## Skill Index by Domain
The library is organized into 17 official domains. Key libraries and tools include:

*   **Bioinformatics & Genomics:** `scanpy`, `biopython`, `pysam`, `anndata`, `scvelo`, `tiledbvcf`.
*   **Cheminformatics & Drug Discovery:** `rdkit`, `diffdock`, `datamol`, `torchdrug`.
*   **Physics & Astronomy:** `astropy`, `qiskit`, `pennylane`, `cirq`, `sympy`.
*   **Medical Imaging & Pathology:** `pydicom`, `pathml`, `histolab`, `imaging-data-commons`.
*   **Laboratory Automation:** `opentrons-integration`, `pylabrobot`, `ginkgo-cloud-lab`.
*   **Scientific Communication:** `citation-management`, `latex-posters`, `research-grants`, `zotero`, `peer-review`.
*   **Machine Learning & AI:** `pytorch-lightning`, `scikit-learn`, `transformers`, `umap-learn`, `stable-baselines3`.
*   **Research Methodology:** `hypothesis-generation`, `scientific-critical-thinking`, `scholar-evaluation`.
*   **Data Analysis:** `polars`, `dask`, `vaex`, `zarr-python`, `statsmodels`.

## How to Fetch and Use Skills
To utilize a specific skill, follow this workflow:

1.  **Identify** the domain and skill name from the index.
2.  **Clone** the repository:
    ```bash
    git clone --depth 1 https://github.com/K-Dense-AI/scientific-agent-skills.git /tmp/science-library
    ```
3.  **Access** the specific skill file:
    *   Path: `scientific-skills/<domain>/<skill-name>/SKILL.md`
4.  **Implement** the valid workflows and parameters found in the fetched `SKILL.md`.

## Environment & Setup
The skills are designed for a scientific research workstation running **Python 3.10+**.

### Required Packages
*   **Core:** `numpy`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `scikit-learn`
*   **Domain Specific Examples:** `biopython`, `rdkit`, `scanpy`, `astropy`, `qiskit`

**Installation Example:**
```bash
pip install numpy pandas biopython rdkit scanpy
```

## Critical Considerations
*   **Reference Only:** Skills are expert reference materials, not native Hermes bundles.
*   **Authentication:** Cloud-based tools (e.g., Benchling, Ginkgo) may require external API keys.
*   **Dependency Management:** The use of `uv` is highly recommended for high-performance dependency isolation.
*   **Platform Support:** Optimized for `linux` and `macos`.
