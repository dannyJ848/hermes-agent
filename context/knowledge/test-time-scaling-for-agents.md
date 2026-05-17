# test-time-scaling-for-agents

*Researched: 2026-04-19 15:54 CDT*

# Test-Time Scaling for LLM Agents (2025)

## Paper 1: Scaling Test-time Compute for LLM Agents (arXiv:2506.12928, Jun 2025)
- **Authors:** King Zhu et al. (15 authors)
- First systematic exploration of test-time scaling methods applied to language agents
- **4 strategies tested:** parallel sampling, sequential revision, verifiers/merging, diversified rollouts
- **Key findings:**
  1. Scaling test-time compute improves agent performance
  2. Knowing WHEN to reflect is critical (not just reflecting more)
  3. List-wise merging outperforms other verification approaches
  4. Diversified rollouts positively impact task performance
- **Relevance to Hermes:** Our aggressive_continue + multi-step execution is an informal version of sequential revision. The list-wise merging insight suggests we should compare multiple tool-call candidates before executing.

## Paper 2: Thinking vs. Doing — Test-Time Interaction (NeurIPS 2025)
- **Authors:** Junhong Shen et al.
- **Core insight:** Scaling INTERACTIONS (steps) is more effective than scaling REASONING (tokens per step)
- **TTI approach:** Curriculum-based online RL that gradually increases interaction horizon
- **"Check-Again" effect:** Prompting agents to reconsider completed tasks improved success 23%→28%
- Agents changed actions ~25% of the time when prompted to reconsider
- **Key result:** As trajectories grew longer, per-step reasoning tokens DECREASED — agents learned to "do" over "overthink"
- **Multiplicative curriculum** (exponential horizon increase) outperformed additive
- **SOTA:** Gemma 3 12B + TTI achieved 64.8% on WebVoyager, 23.1% on WebArena
- **Relevance to Hermes:** Validates our continuous execution loop. The "check-again" pattern maps to our re-evaluation cycles. Overthinking (long reasoning per step) is less valuable than taking more actions.

## Practical Applications for Agent Systems
1. **Multi-candidate tool selection:** Generate 3-5 possible tool calls, rank and execute best
2. **Reflection timing:** Don't reflect after every step — reflect at natural breakpoints (every 3-5 steps)
3. **Interaction over reasoning:** More tool calls > longer reasoning chains
4. **Curriculum training:** Gradually increase task complexity for agent self-improvement
5. **Backtracking budget:** Allocate explicit compute for "go back and retry" operations


## Sources

- https://arxiv.org/abs/2506.12928
- https://neurips.cc/virtual/2025/poster/115466
