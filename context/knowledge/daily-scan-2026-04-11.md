# daily-scan-2026-04-11

*Researched: 2026-04-11 08:06 CDT*

# Daily Intelligence Scan — April 11, 2026

## Key Papers

### 1. ToolTree (ICLR 2026) — MCTS for Tool Planning
- **arXiv:** 2603.12740
- **Key Idea:** Monte Carlo tree search-inspired planning for LLM agent tool use. Uses dual-stage LLM evaluation + bidirectional pruning to explore tool trajectories. Prunes unpromising branches both BEFORE and AFTER tool execution.
- **Results:** ~10% average gain over SOTA on 4 benchmarks (open-set and closed-set).
- **Relevance to SOMA:** The bidirectional pruning approach could improve Hermes' tool selection. Pre-execution pruning aligns with our "weak tools" heuristic — we already score tools before calling them. Post-execution pruning (cutting off failing trajectories early) would be a new capability.

### 2. PCE: Planner-Composer-Evaluator (ICLR 2026) — Uncertainty-Aware Planning
- **arXiv:** 2602.04326
- **Key Idea:** Converts LLM reasoning assumptions into structured decision trees. Internal nodes = environment assumptions, leaves = actions. Scores paths by scenario likelihood, goal-directed gain, and execution cost.
- **Results:** Outperforms communication-centric baselines on C-WAH and TDW-MAT benchmarks while maintaining comparable token usage.
- **Relevance to SOMA:** The "assumption → action tree" pattern is directly applicable to multi-step agent workflows. Could reduce unnecessary tool calls by structuring reasoning traces.

### 3. Utility-Guided Agent Orchestration — Cost/Quality Trade-offs
- **arXiv:** 2603.19896
- **Key Idea:** Treats agent orchestration as an explicit decision problem. Selects among actions (respond, retrieve, tool call, verify, stop) by balancing estimated gain, step cost, uncertainty, and redundancy.
- **Relevance to SOMA:** Maps directly to Hermes' tool dispatch. Our "tool intelligence" scoring is similar but less formal. The redundancy control mechanism (detecting when additional tool calls won't improve results) could help our autonomous loops.

### 4. TRACE — Evaluating Reasoning Trajectories of Tool-Augmented Agents
- **Venue:** OpenReview
- **Key Idea:** Multi-dimensional evaluation framework for tool-augmented LLM agent performance. Goes beyond task success to evaluate reasoning trajectory quality.

## Interesting New Repos (April 11)

| Repo | Description | Stars |
|------|-------------|-------|
| mturac/claude-roundtable | Multi-agent governance for Claude Code — deliberate, vote, dispatch | 2 |
| SAFuDarren/agent-governance-layer | Constitution→Router→Execution governance for skill-based agents | 1 |
| agentnxt/skill-gallery | Agent Skill Benchmark Platform — compare/benchmark skills across LLMs | 0 |
| mwigge/agent-circuit-breaker | Pre-tool-use circuit breaker for Claude Code / OpenCode | 0 |

## Cross-Domain Synthesis

**ToolTree + Utility-Guided Orchestration → Hermes Enhancement Opportunity:**
Both papers converge on the same insight: tool selection should be treated as a search/planning problem, not a reactive prompt-level behavior. Hermes already has tool intelligence scoring (success rates, proven/weak tools), but lacks:
1. Pre-execution trajectory pruning (ToolTree's bidirectional approach)
2. Explicit cost/utility modeling (Utility-Guided's gain vs. cost scoring)
3. Redundancy detection (knowing when additional calls won't help)

These could be combined into a "smart dispatch" layer that sits between task decomposition and tool execution.


## Sources

- https://arxiv.org/abs/2603.12740
- https://arxiv.org/abs/2602.04326
- https://arxiv.org/abs/2603.19896
- https://openreview.net/forum?id=chLlLbI7de
- https://github.com/mturac/claude-roundtable
- https://github.com/SAFuDarren/agent-governance-layer
