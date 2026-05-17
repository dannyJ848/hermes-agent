# reasoning-frameworks-2025-reflact-pr-cot

*Researched: 2026-04-13 18:22 CDT*

# Reasoning Frameworks: ReflAct and PR-CoT (2025)

## ReflAct: World-Grounded Decision Making (KAIST/SNU, 2025)
- **Paper:** arxiv 2505.15182v2
- **Key insight:** ReAct's "thought" steps are often ungrounded — disconnected from actual agent state and goal, causing compounding errors and hallucinations.
- **Solution:** Shift reasoning from planning next actions → continuously reflecting on agent's state relative to its goal. Explicitly ground decisions in states, enforce ongoing goal alignment.
- **Results:** +27.7% over ReAct on average. 93.3% success rate on ALFWorld. Outperforms ReAct+Reflexion and ReAct+WKM combinations.
- **Key takeaway for Hermes:** The "ungrounded thought" problem maps directly to aggressive_continue injection — the agent generates reasoning disconnected from actual state. Goal-state reflection (checking current state vs. desired goal before each action) could reduce no-op loops.
- **Self-correction:** ReflAct self-corrects automatically without external feedback loops.

## PR-CoT: Poly-Reflective Chain-of-Thought (University of Brasilia, 2025)
- **Paper:** arxiv 2601.07780v1
- **Key insight:** Single-dimensional self-correction is insufficient. Multi-perspective reflection catches more errors.
- **Four reflection perspectives:**
  1. Logical consistency check
  2. Information completeness check
  3. Bias and ethical considerations
  4. Alternative solution exploration
- **Implementation:** Pure prompt engineering — no retraining needed. After initial CoT, guides LLM to self-assess across all 4 angles, then synthesizes refined answer.
- **Results:** Significantly outperforms CoT and existing single-reflection methods, especially on ethical decision-making and logical puzzles.
- **Key takeaway for Hermes:** Could enhance autonomous_decide with multi-perspective checks before task selection (e.g., "Is this task logically consistent with current state? Is it complete enough? Are there better alternatives?").

## Cross-domain Synthesis
Both papers converge on the same principle: **reflection must be grounded in concrete state**, not free-form reasoning. For autonomous agents:
1. Before each action, verify state-goal alignment (ReflAct pattern)
2. After each reasoning chain, apply multi-perspective validation (PR-CoT pattern)
3. Self-correction is more effective when structured than when left open-ended


## Sources

- https://arxiv.org/html/2505.15182v2
- https://arxiv.org/html/2601.07780v1
