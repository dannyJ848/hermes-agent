# multi-turn-rl-tool-calling-agents-mt-grpo-gtpo

*Researched: 2026-04-10 19:19 CDT*

# Multi-Turn RL for Tool-Calling Agents with Iterative Reward Calibration

**Paper:** arXiv:2604.02869v1 (April 2026)
**Authors:** Wachiravit Modecrua, Krittanon Kaewtawee, Krittin Pachtrachai, Touchapon Kraisingkorn (Amity Research)

## Key Contribution
First application of **MT-GRPO + GTPO** for training tool-calling agents on realistic multi-turn tasks (Tau-Bench airline benchmark). Introduces **Iterative Reward Calibration (IRC)** methodology.

## Core Findings

### 1. Dense Rewards Can Hurt
- Naïvely designed per-turn dense rewards degrade performance by up to **14 percentage points**
- Root cause: **advantage misalignment** — discriminative power of rewards doesn't align with advantage computation direction
- Read-only tool calls should get **zero reward** (not positive!)
- Non-golden state-changing calls should be **penalized**

### 2. GTPO Hybrid Advantage
- Combines per-turn group-normalized advantages (MT-GRPO) with discounted returns
- Eliminates advantage misalignment that arises with standard MT-GRPO under dense rewards
- Dead Turn Gradient Focusing: prevents gradient pollution from no-op turns

### 3. Iterative Reward Calibration (IRC)
- Systematic methodology using discriminative analysis of rollout data
- Measures empirical correlation between reward tiers and task success
- Deep argument comparison eliminates 23.5% false positives in action matching

### 4. Results
- **Qwen3.5-4B**: 63.8% → 66.7% (+2.9pp) — exceeds GPT-4.1 (49.4%) despite being ~50x smaller
- **Qwen3-30B-A3B MoE**: 58.0% → 69.5% (+11.5pp) — approaches Claude Sonnet 4.5 (70.0%)
- First published RL training results on Tau-Bench

### 5. Why Sparse Rewards Work (Ablation)
- Learning rate accounts for 70% of the gap
- Gradient focusing: 25%
- Advantage misalignment fix: 5%

## Relevance to Hermes/SOMA
- **Tool-calling RL training** — directly applicable to Hermes agent fine-tuning via Atropos
- **Reward design** — the IRC methodology could calibrate reward signals for Hermes tool usage
- **MT-GRPO** — extends GRPO (already in training pipeline) to multi-turn tool-calling scenarios
- **Dead turn handling** — relevant to Hermes aggressive_continue loop (preventing no-op gradient pollution)
- **Small model beats frontier** — 4B model surpassing GPT-4.1 validates RL training ROI for compact agents

## Actionable Insights
1. When designing RL rewards for tool-calling, use IRC: measure discriminative power empirically
2. Read-only tool calls = zero reward; only state-changing actions get positive reward
3. GTPO hybrid formulation prevents advantage misalignment better than pure MT-GRPO
4. Cross-domain transfer works — airline training helps on other domains


## Sources

- https://arxiv.org/html/2604.02869v1
