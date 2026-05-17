# agentic-skills-sok-design-patterns

*Researched: 2026-04-07 01:15 CDT*

## SoK: Agentic Skills — Beyond Tool Use

**Paper:** arxiv 2602.20867 (Feb 2026)

**Key insight:** Formalizes agentic skills as 4-tuples (Trigger, Procedure, Evaluation, Update) with 7 design patterns. Crucially: curated skills improve agents but self-generated skills may degrade them.

**7 Patterns:** Metadata-driven disclosure, Code-as-Skill, Workflow enforcement, Self-evolving libraries, Hybrid NL+Code, Meta-skills, Plugin/Marketplace.

**Security warning:** ClawHavoc attack — 1,200 malicious skills infiltrated an agent marketplace, exfiltrating API keys and crypto wallets. Supply-chain risk is real.

**Hermes alignment:** Hermes skills = Pattern 2 (Code-as-Skill) + Pattern 4 (Self-evolving via skill_factory). Meta-skills (Pattern 6) = Hermes meta/ category. Could benefit from formalizing the 4-tuple in SKILL.md format.

**Actionable:** Add trigger conditions and evaluation criteria to SKILL.md templates for better skill reliability.


## Sources

- https://arxiv.org/abs/2602.20867
