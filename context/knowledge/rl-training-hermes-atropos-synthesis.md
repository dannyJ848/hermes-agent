# RL Training Hermes Atropos Synthesis

*Researched: 2026-04-09 23:16 CDT*

# RL Training for Hermes Atropos Environments — Design Synthesis

Synthesized from 15+ research papers into actionable Atropos environment design. Key recommendations:
1. Use sparse outcome rewards (not dense per-turn) — dense rewards degrade performance by up to 14pp
2. Implement GiGPO dual-level advantage (macro episode + micro anchor states) for >12% gains
3. Add reasoning quality reward to prevent collapse in multi-turn settings
4. Use GTPO hybrid advantage formulation for token+group level optimization
5. Build curriculum: L1 single tools → L2 chains → L3 error recovery → L4 autonomous sessions

## Sources

- arxiv:2604.02869
- arxiv:2505.10978
- internal:hermes-agent/environments/
- internal:wiki/concepts/mt-grpo-tool-calling-agents.md
