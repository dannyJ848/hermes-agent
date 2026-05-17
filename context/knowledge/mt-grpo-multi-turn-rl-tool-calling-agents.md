# MT-GRPO-multi-turn-RL-tool-calling-agents

*Researched: 2026-04-09 14:19 CDT*

# Multi-Turn RL for Tool-Calling Agents with Iterative Reward Calibration

**Paper:** arxiv:2604.02869 (Apr 2026) - Amity Research and Application Center
**Authors:** Wachiravit Modecrua, Krittanon Kaewtawee, Krittin Pachtrachai, Touchapon Kraisingkorn

## Key Innovation
First application of MT-GRPO (Multi-Turn Group Relative Policy Optimization) combined with GTPO (Generalized Token-level Policy Optimization) for training tool-calling agents on realistic multi-turn tasks (Tau-Bench airline benchmark).

## Core Techniques

### 1. MT-GRPO + GTPO Hybrid Advantage
- MT-GRPO normalizes rewards within rollout groups at each turn position
- GTPO applies discounted returns across turns
- Hybrid formulation eliminates **advantage misalignment** — a discovered problem where dense per-turn rewards degrade performance by up to 14pp

### 2. Iterative Reward Calibration (IRC)
- Naïve dense per-turn rewards HURT performance (counterintuitive finding)
- IRC uses empirical discriminative analysis of rollout data to design per-turn rewards
- Systematic calibration prevents reward discriminativeness from misaligning with advantage direction

### 3. Dead Turn Gradient Focusing
- Prevents gradient waste on uninformative turns
- Focuses learning signal on turns that actually matter for task success

## Results (Tau-Bench Airline)
| Model | Before | After | Delta |
|-------|--------|-------|-------|
| Qwen3.5-4B | 63.8% | 66.7% | +2.9pp |
| Qwen3-30B-A3B | 58.0% | 69.5% | +11.5pp |

- Trained 4B model **exceeds** GPT-4.1 (49.4%) and GPT-4o (42.8%) — ~50x smaller
- 30.5B MoE approaches Claude Sonnet 4.5 (70.0%)
- First published RL training results on Tau-Bench

## Key Insights
1. **Sparse rewards accidentally work better than naïve dense rewards** — learning rate explains 70% of the gap, gradient focusing 25%, advantage misalignment 5%
2. **Cross-domain transfer** works — trained models generalize beyond airline domain
3. **Small models can compete with frontier** via targeted RL training on domain-specific tool use

## Relevance to Hermes Agent
- Directly applicable to Atropos RL environments for Hermes tool-calling optimization
- IRC methodology could improve reward design for our distillation pipeline
- Dead Turn Gradient Focusing could filter out uninformative tool calls during training
- Proves MoE models (like Qwen3-30B-A3B) benefit most from multi-turn RL


## Sources

- https://arxiv.org/abs/2604.02869
- https://arxiv.org/html/2604.02869v1
