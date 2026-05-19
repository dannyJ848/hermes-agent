# mt-grpo-gtpo-tool-calling-rl

*Researched: 2026-04-10 18:14 CDT*

# MT-GRPO + GTPO for Multi-Turn Tool-Calling RL Training

**Paper:** arXiv:2604.02869v1 (Apr 2026) — First MT-GRPO + GTPO applied to tool-calling agents on Tau-Bench.

## Key Findings
1. **Dense rewards hurt** if misaligned — naïve per-turn rewards degraded performance by 14pp
2. **IRC (Iterative Reward Calibration):** Read-only tool calls → zero reward. Penalize non-golden state changes. Deep argument comparison eliminates 23.5% false positives
3. **GTPO hybrid advantage** eliminates misalignment from standard MT-GRPO
4. **4B model beats GPT-4.1** (66.7% vs 49.4%) on Tau-Bench airline
5. **Dead Turn Gradient Focusing** prevents wasted signal on non-productive turns

## Implications for Hermes
- IRC methodology directly applicable to Atropos environments
- Reward design should be empirically validated, not intuitively assigned
- Cross-domain transfer from Tau-Bench generalizes to other tool-use tasks

## Sources

- https://arxiv.org/html/2604.02869v1
