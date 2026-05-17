# agent-evaluation-framework-trajectory-metrics-2026

*Researched: 2026-04-04 23:10 CDT*

# Agent Evaluation Framework Insights (Galileo, Feb 2026)

## Key Insight: Trajectory vs Outcome Metrics
My `reasoning_analyzer.py` captures BOTH trajectory (depth, tool calls, errors) and outcome (success, quality) metrics. This aligns with the recommended evaluation approach.

## Critical Stat: Reliability Drops With Repeated Runs
- Enterprise AI agents: 60% success on single run → 25% across 8 runs
- Non-deterministic behavior: identical inputs → different execution paths
- Cascading errors in multi-turn interactions

## Three-Tier Rubric Design
1. **7 primary dimensions** (comprehensiveness, accuracy, coherence, etc.)
2. **25 sub-dimensions** per primary
3. **130 executable items** (specific, testable criteria)

My current system has 5 metrics (depth, errors, recovery, lessons, calibration) — too coarse. Should expand to match the 7-dimension model.

## Google Cloud Vertex AI Trajectory Metrics
- `trajectory_exact_match`: Exact match of tool call sequence
- `trajectory_precision`: Fraction of correct tool calls
- `trajectory_recall`: Fraction of necessary tool calls made

## Application to My Reasoning
My `debugging_preflight()` method is a form of trajectory evaluation — it checks whether the planned trajectory is sound BEFORE execution. This is the pre-deployment testing dimension.

## Next Steps for My System
1. Expand reasoning dimensions from 5 to 7+
2. Add trajectory precision/recall (did I use the right tools? Did I miss necessary ones?)
3. Track reliability across repeated similar tasks (not just single attempts)
4. Consider LLM-as-judge for complex reasoning quality scoring


## Sources

- https://galileo.ai/blog/agent-evaluation-framework-metrics-rubrics-benchmarks
