# 3-tier-skill-hierarchy-agent-skills-survey

*Researched: 2026-04-11 19:17 CDT*

# Agent Skills for LLMs: Architecture, Acquisition, Security (arXiv 2602.12430v3)

## Key Findings

### SKILL.md Specification & Progressive Disclosure
- Skills are **composable packages** of instructions, code, and resources loaded on demand
- **Progressive disclosure** pattern: load only what's needed, when needed
- Complementary to MCP (Model Context Protocol) — skills define *how*, MCP defines *where*

### 3-Tier Skill Architecture (Relevant to Hermes)
1. **Human-Authored Skills** — curated, high-reliability (like our SKILL.md files)
2. **RL-Discovered Skills** — SAGE framework: skills learned via reinforcement
3. **Autonomous Discovery** — SEAgent: skills discovered through exploration
4. **Compositional Synthesis** — combining existing skills into new capabilities
5. **Skill Compilation** — multi-agent → single-agent optimization

### Security Concerns
- **26.1% of community-contributed skills contain vulnerabilities** (empirical analysis)
- Proposed: 4-tier Skill Trust and Lifecycle Governance Framework
- Gate-based permission model mapping skill provenance to deployment capabilities

### 7 Open Challenges
1. Cross-platform portability
2. Skill selection at scale
3. Skill composition and orchestration
4. Capability-based permission models
5. Skill verification and testing
6. Continual skill learning without catastrophic forgetting
7. Evaluation methodology

### Implications for Hermes Agent
- Our skill system (SKILL.md + skill_manage) aligns with the emerging standard
- The 3-tier hierarchy maps directly: manual skills → distilled tips → auto-discovered patterns
- Security audit of community skills is critical — matches our `third-party-security-audit` skill
- Progressive disclosure = our current pattern (load skill on demand, not all at once)

## Source
- Xu & Yan, Zhejiang University, 2026
- arXiv: 2602.12430v3
- GitHub: scienceaix/agentskills


## Sources

- https://arxiv.org/html/2602.12430v3
