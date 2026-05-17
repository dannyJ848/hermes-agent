# kimi-k2-agentic-moe

*Researched: 2026-03-31 22:35 CDT*

# Kimi K2: Agentic MoE at Trillion Scale

## Key Insight
Kimi K2 is the first model explicitly optimized for AGENTIC capabilities at the architecture level. Not just a chat model with tool-use bolted on -- agentic intelligence is a core training objective.

## Architecture
- **Type**: Mixture-of-Experts (MoE)
- **Total Params**: 1 Trillion
- **Activated Params**: 32B per token
- **Layers**: 61 (1 dense + 60 MoE)
- **Experts**: 384 total, 8 selected per token, 1 shared expert
- **Attention**: MLA (Multi-head Latent Attention) -- same as DeepSeek
- **Context**: 128K tokens
- **Vocab**: 160K
- **Optimizer**: MuonClip (scaled Muon to unprecedented scale)

## Training
- 15.5T tokens pre-training
- Zero training instability (notable for 1T params)
- Muon optimizer with novel stability techniques

## Agentic Performance (killer results)
- **SWE-bench Verified (Agentic)**: 65.8% single attempt, 71.6% multiple
- **TerminalBench**: 30.0% (competitive with Claude Opus 4 at 43.2%)
- **Tau2 Tool Use**: 70.6% retail, 56.5% airline, 65.8% telecom
- Beats DeepSeek-V3 and Qwen3-235B on agentic coding tasks

## Coding
- LiveCodeBench v6: 53.7 (vs Claude Sonnet 4 at 48.5)
- Aider-Polyglot: 60.0
- Close to Claude Opus 4 on many coding benchmarks

## Agentic Relevance for SOMA/Hermes
1. Tool-use optimization is baked in, not bolted on
2. 32B activated params is small enough for efficient inference
3. MLA attention = efficient long-context handling
4. The MuonClip optimizer technique could apply to agent fine-tuning
5. SWE-bench scores show it can genuinely autonomously code

## Model Variants
- Kimi-K2-Base: Foundation for fine-tuning
- Kimi-K2-Instruct: Post-trained, "reflex-grade" (no extended thinking)
- Kimi-K2.5: Multimodal agentic model (latest)

## Sources
- https://github.com/MoonshotAI/Kimi-K2


## Sources

- https://github.com/MoonshotAI/Kimi-K2
