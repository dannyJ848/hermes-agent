# rl-training-agentic-2026

*Researched: 2026-04-10 19:58 CDT*

# RL Training for Agentic AI (2025-2026 Advances)

## Key Finding 1: Agent Lightning (Microsoft Research, Dec 2025)

**Problem:** Adding RL to AI agents requires extensive code rewrites, discouraging adoption.

**Solution:** Agent Lightning is middleware that separates agent execution from model training:
- Converts agent behavior into standardized state-action-reward transitions
- **Hierarchical RL (LightningRL):** Breaks multi-step agent runs into individual LLM calls with per-call credit assignment
- Compatible with existing single-step RL algorithms (PPO, GRPO) without modification
- LightningStore as central data exchange between agent runner and training algorithm
- No code rewrites needed — works as middleware

**Architecture:**
- Agent Runner: manages agents, distributes work, collects results (runs separately from GPUs)
- Algorithm Server: trains models, hosts LLMs, orchestrates RL cycle
- LightningStore: shared repository for all data exchanges

**Key insight:** Instead of stitching all multi-step content into one long sequence, LightningRL treats each LLM call as independent with its own reward. This avoids long-sequence degradation and scales cleanly.

## Key Finding 2: GPT-OSS Agentic RL (LinkedIn/HuggingFace, Jan 2026)

**Problem:** Agentic RL for MoE models (GPT-OSS) has training instability — exploding KL divergence and entropy.

**Root Cause:** In MoE architectures, the gating network routes to different experts across two forward passes. This causes `log(π(a|s)) ≠ log(π_old(a|s))` even for on-policy data, violating PPO's core assumption.

**Fix:** When on-policy is guaranteed, set `old_log_prob = log_prob.detach()` to force the importance ratio to exactly 1. This bypasses MoE's non-deterministic routing.

**Additional fixes:**
- Attention sink support in FlashAttentionV3 for GPT-OSS's attention patterns
- Sequence parallel with Flash Attention V3 for memory efficiency
- FSDP memory optimization for repeated MoE expert materialization

## Key Finding 3: GRPO++ and GAP

**GAP (Graph-Based Agent Planning):** Tsinghua University (Oct 2025) — parallel tool use with RL, using graph-based planning to coordinate multi-tool execution.

**Retool:** RL for strategic tool use in LLMs (arXiv 2504.11536) — trains models to delegate computation to code tools during reasoning.

## Relevance to Hermes Agent

1. **Agent Lightning pattern** could be applied to Hermes tool-calling training — treat each tool call as an independent transition with credit assignment
2. **LightningRL's hierarchical approach** matches Hermes's tool-call-per-step architecture naturally
3. **MoE log-prob mismatch** is relevant if using MoE base models for fine-tuning
4. **Parallel tool use (GAP)** relates to Hermes's delegate_parallel patterns


## Sources

- https://www.microsoft.com/en-us/research/blog/agent-lightning-adding-reinforcement-learning-to-ai-agents-without-code-rewrites/
- https://huggingface.co/blog/LinkedIn/gpt-oss-agentic-rl
