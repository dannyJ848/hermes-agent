# TRACE Capability-Targeted Agentic Training (arXiv:2604.05336)

*Researched: 2026-04-09 14:52 CDT*

# TRACE: Capability-Targeted Agentic Training

**Source:** arXiv:2604.05336 (Apr 7, 2026)

TRACE contrasts successful/failed agent trajectories to identify lacking capabilities, synthesizes targeted RL training environments for each gap, trains per-capability LoRA adapters, and routes to the right adapter at inference. Results: +14.1 pts on τ²-bench, +7 perfect ToolSandbox scores. Outperforms GRPO by +9.2 and GEPA by +7.4 pts. Key insight: target training at specific capability deficits rather than training on all tasks equally. Maps directly to Hermes domain_certainty.py — each low-confidence domain could become a TRACE-style training target.

## Sources

- https://arxiv.org/abs/2604.05336
