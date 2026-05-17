# TRACE-capability-targeted-agentic-training-apr2026

*Researched: 2026-04-08 11:34 CDT*

# TRACE: Capability-Targeted Agentic Training
**Paper**: arXiv:2604.05336 (April 2026)
**Authors**: Hangoo Kang, Tarun Suresh, Jon Saad-Falcon, Azalia Mirhoseini

## Key Innovation
End-to-end system for environment-specific agent self-improvement that identifies capability deficits through contrastive analysis.

## Method
1. **Contrast trajectories**: Compare successful vs failed trajectories for same task type
2. **Identify capability gaps**: Pinpoint which specific capabilities are lacking
3. **Synthesize training environments**: Create targeted mini-environments that reward exercising the specific lacking capability
4. **Train per-capability LoRA adapters**: Lightweight adapters, one per capability
5. **Route at inference**: Select relevant adapter based on task type

## Results
- +14.1 points on tau-squared-bench (customer service)
- +7 perfect scores on ToolSandbox (tool use)
- Outperforms monolithic GRPO by +9.2 points
- Outperforms GEPA by +7.4 points
- Scales more efficiently than baselines with same rollout budget

## Applications to Evey
- Contrastive failure analysis for identifying which capabilities need improvement
- Per-capability tip injection instead of monolithic injection
- Synthetic training environments for specific failing tools
- LoRA-style specialization (already doing this with ERL task-context retrieval)


## Sources

- https://arxiv.org/abs/2604.05336
