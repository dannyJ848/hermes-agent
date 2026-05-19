# mars-metacognitive-self-improvement

*Researched: 2026-04-04 20:12 CDT*

# MARS: Metacognitive Agent Reflective Self-improvement (arXiv:2601.11974)

## Core Idea
Self-improvement in a SINGLE recurrence cycle, not multi-turn loops.
Combines two types of reflection from educational psychology:

1. **Principle-based reflection**: Abstract normative rules to avoid errors
   - "When I fail at X, it's usually because of Y. Rule: Always check Y first."
   
2. **Procedural reflection**: Step-by-step strategies for success
   - "When doing X, follow these steps: 1... 2... 3..."

## How It Works
- Phase 1: Individual failure analysis (classify each failure by type and topic)
- Phase 2: Type-topic grouping (cluster similar failures)
- Phase 3: Enhancement generation (synthesize rules + procedures from clusters)
- Hybrid selection: Pick the best enhancement variant

## Results
Outperforms Self-Refine, Reflexion, and Gödel Agent on 6 benchmarks.
Significantly less computational overhead (single cycle vs recursive loops).

## What We Should Adopt
Our iteration engine should use the MARS pattern:
1. After each task, analyze: Did it succeed or fail? What type of failure?
2. Group failures by type (TS error, API timeout, wrong approach, etc.)
3. Generate BOTH a principle ("Never trust exit_code 1 for diagnostic commands")
   AND a procedure ("For debugging: 1) reproduce error, 2) isolate, 3) fix, 4) verify")
4. Store both in the iteration engine for next-cycle retrieval


## Sources

- https://arxiv.org/html/2601.11974v1
