# agentsm-semantic-memory-sql

*Researched: 2026-04-08 02:20 CDT*

# AgentSM: Semantic Memory for Agentic Text-to-SQL

**Source:** arXiv 2601.15709 (Biswal et al., AWS/Berkeley/Oracle/Snowflake)

## Key Innovation
Instead of raw scratchpads or vector retrieval for agent memory, AgentSM captures prior execution traces as **structured programs** that directly guide future reasoning. This enables systematic reuse of reasoning paths.

## Results
- 25% reduction in average token usage
- 35% reduction in trajectory length
- 44.8% accuracy on Spider 2.0 Lite (SOTA)

## Actionable Implications for Hermes Agent
1. **Trajectory synthesis** — Store successful tool-call sequences as reusable "composite tools" (AgentSM's term). When cerebrum sees a similar task pattern, inject the composite tool instead of forcing re-exploration.
2. **Semantic memory over raw scratchpads** — Our distilled_tips table is a flat list. AgentSM shows value in structured trajectory programs: `input_pattern → tool_sequence → expected_output`. This could improve tool_planner.py's MCTS scoring.
3. **Repeated exploration is the #1 waste** — AgentSM found that data exploration is inherently repetitive. Our agent wastes turns re-discovering the same codebase patterns. A trajectory cache keyed on task-type would eliminate this.
4. **Composite tools pattern** — Bundle frequent tool sequences (read_file→patch→terminal verify) into single "meta-tools" that skip intermediate steps. This directly addresses our 54.1% code_debug success rate — pre-bundling the pattern could push it higher.


## Sources

- https://arxiv.org/html/2601.15709v1
