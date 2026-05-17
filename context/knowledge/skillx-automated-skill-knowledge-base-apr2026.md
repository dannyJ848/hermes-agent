# skillx-automated-skill-knowledge-base-apr2026

*Researched: 2026-04-08 11:41 CDT*

# SkillX: Automated Skill Knowledge Base Construction
**Paper**: arXiv:2604.04804 (April 2026)
**Authors**: Chenxi Wang et al. (11 authors)

## Key Innovation
Fully automated framework for constructing plug-and-play skill knowledge bases that transfer across agents and environments. Uses GLM-4.6 as backbone.

## Three Synergistic Innovations
1. **Multi-Level Skills Design**: 3-tier hierarchy — strategic plans, functional skills, atomic skills
2. **Iterative Skills Refinement**: Automatically revises skills based on execution feedback
3. **Exploratory Skills Expansion**: Proactively generates and validates novel skills

## Results
- Tested on AppWorld, BFCL-v3, tau-squared-Bench
- Consistently improves task success and execution efficiency on weaker base agents
- Hierarchical experience representations enable generalizable learning

## Gap Analysis vs Evey's Distillation
- **What we have**: Atomic tips (single tool patterns), confidence scoring, SAGE reward, ERL retrieval
- **What we lack**: Functional skill level (multi-step chains), automatic revision on failure, exploratory expansion with validation
- **Action items**: (1) Add multi-step tip chains, (2) implement revision-on-failure loop, (3) validate new tips against held-out calls


## Sources

- https://arxiv.org/abs/2604.04804
