# agi-experience-procedural-memory

*Researched: 2026-04-12 02:01 CDT*

# AGI Experience: Procedural Memory for AI Agents

## Key Paper: Mem^p (Fang et al. 2025) — arxiv 2508.06433

**Core insight:** LLM agents suffer from brittle procedural memory — either hand-crafted prompts or entangled in static parameters. Mem^p proposes a learnable, updatable, lifelong procedural memory.

**Three operations:**
1. **Build** — Distill past agent trajectories into (a) fine-grained step-by-step instructions and (b) higher-level script-like abstractions
2. **Retrieval** — Scaling memory retrieval improves agent performance
3. **Update** — Dynamic regimen that continuously updates, corrects, and deprecates contents

**Key findings:**
- Procedural memory boosts accuracy and cuts trial count significantly
- Memory built from stronger models transfers to weaker models (distillation property)
- Evaluated on TravelPlanner and ALFWorld benchmarks

## Qualia Wave Framework (Rosario & Wang, 2025)

**Epistemological split:**
- **Mimetic intelligence** — Current LLMs that reproduce human language patterns
- **Experiential intelligence** — Learns through real-world consequences

**Qualia Vector:** Models subjective consciousness as a quantifiable, propagating wave. Used to generate intrinsic motivation by minimizing prediction error between world model and conscious experience.

## Relevance to Hermes Agent

Our cerebrum_memory.db distilled_tips table is essentially a primitive procedural memory. The Mem^p framework suggests we should:
1. Store both fine-grained tips AND higher-level skill abstractions
2. Implement continuous update/correction/deprecation cycles
3. Test transferability — tips distilled from strong models should help weaker ones

## Related Resources
- TsinghuaC3I/Awesome-Memory-for-Agents — curated paper list on agent memory taxonomy
- Agent-Memory (Hightower) — Rust-powered append-only episodic memory for AI coding assistants
- LessWrong: Episodic memory in AI agents poses new safety risks


## Sources

- https://arxiv.org/html/2508.06433v2
- https://www.linkedin.com/posts/dylanrosario_towards-artificial-general-intelligence-activity-7389519244247359488-olbY
- https://github.com/TsinghuaC3I/Awesome-Memory-for-Agents
