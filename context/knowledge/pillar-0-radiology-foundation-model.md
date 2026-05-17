# pillar-0-radiology-foundation-model

*Researched: 2026-04-03 21:03 CDT*

# Pillar-0: Open Radiology Foundation Model

**Source:** YalaLab (UC Berkeley + UCSF), published 2025-2026
**Repo:** github.com/YalaLab/pillar-0
**Paper:** arxiv.org/html/2511.17803v1

## What It Does
- First open-source radiology foundation model that processes 3D CT/MRI volumes directly (not 2D slices)
- Pretrained on 155,392 scans: 42,990 abdomen-pelvis CTs, 86,411 chest CTs, 14,348 head CTs, 11,543 breast MRIs
- Recognizes 366+ radiologic findings with mean AUC of 0.87

## Key Results
- Outperforms Google MedGemma (.76 AUC), Microsoft MI2 (.75), Alibaba Lingshu (.70) by 10-17%
- Lung cancer risk: 3.0 C-index improvement over Sybil-1
- Data efficient: >95 AUC with only 1/20 of training data

## Relevance to SOMA
- Could power diagnostic imaging features for medical education
- Patient education: "Your CT shows X, here's what that means" in EN/ES
- Requires GPU inference — may need cloud API or on-device quantization
- RATE framework for structured label extraction is independently useful

## Integration Notes
- Python-based, weights available
- Needs significant GPU resources for inference
- Best deployed via API endpoint, not on-device


## Sources

- https://yalalab.github.io/pillar-0/
- https://arxiv.org/html/2511.17803v1
- https://www.itnonline.com/content/researchers-release-new-ai-model-medical-imaging
