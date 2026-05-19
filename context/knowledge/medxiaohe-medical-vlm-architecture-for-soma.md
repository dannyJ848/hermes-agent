# MedXIAOHE Medical VLM Architecture for SOMA

*Researched: 2026-04-04 21:42 CDT*

# MedXIAOHE: Medical VLM Architecture Insights for SOMA

## Source
- **Paper**: "MedXIAOHE: A Comprehensive Recipe for Building Medical MLLMs" (ByteDance XiaoHe Medical AI)
- **URL**: https://arxiv.org/html/2602.12705v1
- **Date**: February 2026

## Key Architecture Insights
1. **Entity-Aware Continual Pretraining**: Organizes heterogeneous medical corpora via Medical Entity Tree (MET) — hierarchical clustering of medical entities to broaden knowledge coverage and reduce long-tail gaps
2. **Multi-stage Training**: Continual pretraining → Mid-training (KG-guided QA + multi-expert reject sampling + structured CoT) → Post-training (SFT + RL with multi-layered hybrid reward)
3. **Agentic Reasoning**: Tool-augmented agentic training enabling multi-step diagnostic reasoning with verifiable decision traces
4. **Medical DeepResearch**: Agent can autonomously research medical questions with image analysis

## SOMA-Relevant Techniques
1. **Medical Entity Tree**: SOMA could use a similar hierarchical structure for bilingual EN/ES medical terminology mapping
2. **Structured CoT**: Chain-of-thought reasoning for anatomy identification in SOMA's quiz mode
3. **Grounding**: Visual grounding (pointing to anatomical structures in 3D model) — directly applicable to SOMA
4. **RFT-Enhanced Curriculum RL**: Progressive difficulty for anatomy learning modules

## Performance
- SOTA across 30+ medical benchmarks
- Surpasses closed-source multimodal systems on multiple capabilities
- Low-hallucination long-form report generation

## SOMA Integration Ideas
- Build a Medical Entity Tree for bilingual anatomy terms
- Use curriculum learning patterns for progressive anatomy education
- Apply visual grounding concept to 3D anatomy model (click → learn)


## Sources

- https://arxiv.org/html/2602.12705v1
