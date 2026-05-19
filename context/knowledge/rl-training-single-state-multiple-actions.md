# rl-training-single-state-multiple-actions

*Researched: 2026-04-09 17:06 CDT*

# RL Training: Single State Multiple Actions (Android Coach, Apr 2026)

**Paper:** Android Coach: Improve Online Agentic Training Efficiency with Single State Multiple Actions
**Authors:** Guo Gan et al. (arXiv:2604.07277, Apr 8 2026)
**Domains:** cs.LG, cs.AI

## Key Insight
Current RL training for agents uses "Single State Single Action" (SSSA) — one state-action pair per rollout step. This wastes expensive emulator states. **Single State Multiple Actions (SSMA)** samples multiple actions per state without additional emulator overhead by learning a critic that estimates action values.

## Technique
1. **Critic-based coaching:** Learn a value critic that estimates action quality for a given state
2. **Process reward model integration:** Use PRM to ensure critic reliability
3. **Group-wise advantage estimator:** Based on averaged critic outputs across sampled actions
4. **No extra emulator cost:** Multiple actions are sampled offline from the critic, not from the emulator

## Results
- +7.5% success rate on AndroidLab over UI-TARS-1.5-7B
- +8.3% success rate on AndroidWorld over UI-TARS-1.5-7B
- **1.4x higher training efficiency** than PPO and GRPO at matched success rates

## Application to Hermes Agent RL Training
- Our Atropos environments could benefit from SSMA: instead of single action per state, sample multiple tool calls per context and let a critic rank them
- Process reward model aligns with our 3-component reward model (answer quality, format quality, execution quality)
- Group-wise advantage could improve our GRPO training signal without more API calls
- Key insight: emulator/API cost dominates — SSMA amortizes that cost across multiple learning signals

## Cross-Domain Synthesis
This technique generalizes beyond Android agents to ANY RL scenario where environment interaction is expensive (API calls, browser automation, terminal execution). The critic acts as a "world model simulator" for cheap action evaluation.


## Sources

- https://arxiv.org/abs/2604.07277
