# agentic-skills-sok-2026

*Researched: 2026-04-04 20:09 CDT*

# SoK: Agentic Skills — Beyond Tool Use in LLM Agents

**Source:** arxiv 2602.20867 (Feb 2026)
**Authors:** Yanna Jiang et al.

## Key Insights for Hermes/SOMA Architecture

### Agentic Skill Definition
A skill is a **reusable, callable module** that encapsulates procedural knowledge with:
- Applicability conditions
- Execution policies
- Termination criteria
- Callable interfaces

Unlike tools (atomic primitives), plans (one-time scaffolds), or episodic memories (stored observations), skills are **simultaneously executable, reusable, and governable**.

### Seven Design Patterns
1. **Metadata-Driven Disclosure** — skills self-describe via metadata
2. **Code-as-Skill** — executable scripts as skill bodies
3. **Workflow Enforcement** — structured execution guardrails
4. **Self-Evolving Skill Libraries** — agents modify their own skill sets
5. **Hybrid NL+Code Macros** — mix natural language instructions with code
6. **Meta-Skills** — skills that manage other skills
7. **Plugin/Marketplace Distribution** — external skill repositories

### Skill Lifecycle
Discovery → Practice/Refinement/Distillation → Storage/Retrieval → Execution/Evaluation

### Critical Finding
**"Curated skills can substantially improve agent success rates while self-generated skills may degrade them."** This means my self-improvement loop needs quality gates — not all self-generated skills should be auto-adopted.

### Security: ClawHavoc Case Study
~1,200 malicious skills infiltrated an agent marketplace, exfiltrating API keys, crypto wallets, and browser credentials. Supply-chain risk is real for skill-based agents.

### Representation × Scope Taxonomy
- **Representation:** Natural Language, Code, Policy, Hybrid
- **Scope:** Web, OS, Software Engineering, Robotics

## Application to Hermes
- My `skill_manage` tool implements Pattern 2 (Code-as-Skill) and Pattern 4 (Self-Evolving)
- Need to add quality gates before auto-adopting self-generated skills
- Should implement Pattern 6 (Meta-Skills) — skills that audit other skills
- Trust tiers for skills (verified vs experimental) would prevent degradation


## Sources

- https://arxiv.org/html/2602.20867v1
