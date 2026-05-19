---
name: biomimetic-architecture
description: >
  Design complex systems by first researching their biological/natural analogs
  in depth, extracting design principles from evolution's solutions, then mapping
  biological mechanisms to computational equivalents. Use when building systems
  that have natural counterparts (memory, vision, language, immune, neural, evolution).
trigger: >
  When designing a system with a clear biological analog, or when Danny redirects
  to "research how X works in nature first." Also when architecture feels ad-hoc
  and could benefit from principled biological grounding.
---

# Biomimetic Architecture Design

## Why
Natural systems have been optimized by billions of years of evolution. Skipping the
biology leads to reinventing mechanisms poorly. Danny explicitly values this approach:
"do a deep dive research on how human memory works, and try to parallel this system to it."

## Steps

### 1. Deep-Dive Research (Parallel Delegation)
Use `delegate_parallel` with 2-3 research tasks targeting the biological system:

- **Mechanism Research**: How does the biological system actually work? Get specific:
  durations, capacities, transfer mechanisms, failure modes.
- **Computational Models**: What existing AI/CS work maps to these biological systems?
  (ACT-R, CLS, MemGPT, HRR, etc.) These are reference implementations.
- **Failure/Disorder Research**: What breaks when parts of the system fail? Each
  disorder teaches a design principle.

### 2. Extract Design Principles
For each biological mechanism, extract a concrete design principle:
- Capacity limits -> buffer sizes
- Consolidation phases -> pipeline stages
- Decay curves -> TTL/relevance scoring
- Emotional salience -> priority weighting
- Sleep replay -> background consolidation cron

### 3. Map Biological to Computational
Create a literal mapping table. Example for memory:

| Biological | Computational | Key Constraint |
|---|---|---|
| Sensory memory | Input buffer | Millisecond TTL, high throughput |
| Working memory | Active context | 4+-1 chunks, rehearsal needed |
| Hippocampus | Episodic store | Fast learning, temporal context |
| Neocortex | Semantic KB | Slow consolidation, trust scoring |
| Amygdala | Salience scorer | Emotional modulation |
| Sleep (SWS) | Consolidation cron | Episodic to semantic transfer |

### 4. Build Bottom-Up
Implement the lowest layer first (raw input), then stack upward. Each layer should:
- Have independent failure modes (survives other layers going down)
- Define clear promotion/consolidation criteria to the next layer
- Implement its own decay/pruning mechanism

### 5. Validate with Disorder Tests
Test each "disorder scenario" after building:
- What if episodic layer dies? Does semantic still work?
- What if salience scoring breaks? Does everything become equally important?
- What if consolidation never runs? Does episodic overflow?
- What if trust scores decay to zero? Can the system recover?

## Pitfalls
- Don't over-literal the biology. Map principles, not implementation details.
- Don't skip the research phase. "I already know how memory works" means you know
  the pop-sci version, not the design-relevant details.
- Watch for Python version issues with `dict | None` type hint syntax (requires 3.10+).
  Use `Optional[dict]` for compatibility.
- Ghost imports (importing classes that don't exist) will silently fail if you
  renamed/removed something mid-design. Always run smoke tests after writing.

## Example: Cerebrum Memory System
Built `plugins/memory/cerebrum/` -- a 4-layer biomimetic memory provider for Hermes Agent:
- Sensory Buffer (30s TTL) -> Working Memory (5 slots) -> Episodic Buffer (200 turns) -> Semantic Store (Holographic HRR)
- Consolidation pipeline mirrors sleep phases
- Salience scoring mirrors amygdala modulation
- Trust scoring + provenance prevents Korsakoff-style confabulation
- Each layer survives independent failure (HM modularity)
- Research sources: Baddeley WM model, Cowan's 4+-1, Ebbinghaus forgetting curve, Ribot's law,
  HM/Clive Wearing/Korsakoff disorder lessons, McClelland CLS
