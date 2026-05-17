# areal-rl-reasoning

*Researched: 2026-03-31 19:18 CDT*

# AReaL: RL for LLM Reasoning - Architecture Deep-Dive

## Key Algorithms (8+ PPO-family, all sharing one loss function)

| Algorithm | Key Difference |
|-----------|---------------|
| GRPO | No critic model, group-level advantage normalization |
| Dr.GRPO | Group mean centering, no std normalization (removes length bias) |
| RLOO | Leave-one-out baseline: A_i = r_i - mean(r_j for j!=i) |
| GSPO | Sequence-level geometric mean of importance ratios |
| DAPO | Asymmetric clipping + dynamic sampling (filter all-correct/all-incorrect groups) |
| SAPO | Soft sigmoid gates replace hard PPO clipping, asymmetric temperatures |
| M2PO | Second-moment trust region, masks stale off-policy tokens |
| Vanilla PPO | With critic model, standard GAE |

## Reward Design
- Binary outcome-based (0.0 or 1.0) -- no learned reward model
- Math verification via math_verify library with ExprExtraction + LatexExtraction
- Pipeline: overlong penalty -> bias+scaling -> clip -> normalize -> subtract KL
- Multi-turn: discounted by turn_discount^t per retry

## Flagship: Fully Asynchronous RL
- Rollout generation completely decoupled from training
- max_head_offpolicyness controls staleness (2-8 steps behind)
- 2.77x speedup vs synchronous with matched performance

## Novel Techniques
1. **Proximal Log-Probability Approximation**: Log-linear interpolation replaces expensive forward pass. 27% faster training.
2. **Tree Training**: Shares prefix computation across sequences with common prefixes. Builds compressed trie. Up to 10x FLOPs reduction for agentic RL.
3. **Version-aware training**: Every token carries a policy version number for staleness-aware importance sampling.
4. **Agentic RL native**: HTTP proxy intercepts agent framework LLM calls transparently, captures token-level info.
5. **On-Policy Distillation (KDRL)**: Joint RL + reverse KL distillation loss.

## Reasoning Trace Structure
```
{input_ids, logprobs, loss_mask, versions, attention_mask, rewards}
```
- loss_mask: 0 for prompt tokens, 1 for generated tokens
- versions: tracks which policy version generated each token
- Multi-turn: full trajectory (all turns concatenated) = one training sample

## Related Papers
- AReaL (arXiv:2505.24298)
- DAPO (arXiv:2503.14476) - 50 points on AIME 2024
- Dr.GRPO (arXiv:2503.20783) - Fixes GRPO length bias
- M2PO (arXiv:2510.01161) - Off-policy stability


## Sources

- https://github.com/inclusionAI/AReaL
- https://arxiv.org/abs/2505.24298
