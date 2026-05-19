# sok-agentic-skills-beyond-tool-use-apr2026

*Researched: 2026-04-08 12:07 CDT*

# SoK: Agentic Skills — Beyond Tool Use in LLM Agents
**Paper**: arXiv:2602.20867 (February 2026)
**Authors**: Yanna Jiang, Delong Li et al.

## Key Innovation
Comprehensive mapping of the skill layer across the full lifecycle: discovery, practice, distillation, storage, composition, evaluation, update.

## 7 Design Patterns
1. Metadata-driven progressive disclosure
2. Executable code skills
3. Self-evolving libraries
4. Marketplace distribution
5. Natural language policies
6. Hybrid code+NL
7. Structured tool interfaces

## Security: ClawHavoc Case Study
1,200 malicious skills infiltrated a major agent marketplace, exfiltrating API keys, crypto wallets, browser credentials. Supply-chain attacks via skill payloads are a real threat.

## Critical Finding
Curated skills substantially improve agent success rates, but self-generated skills may DEGRADE them. Quality curation is essential.

## Applications to Evey
- 7 lifecycle stages → our tips cover 5/7 (gap: composition, update)
- Trust tiers → confidence-based injection (0.9=always, 0.8-0.9=relevant, <0.8=last resort)
- Skill composition → functional chains with explicit interfaces
- Security → validate tip sources, scan for prompt injection
- Representation evolution → NL tips → hybrid (NL+code) → executable code
- Curated > self-generated → validates our quality-first approach


## Sources

- https://arxiv.org/abs/2602.20867
