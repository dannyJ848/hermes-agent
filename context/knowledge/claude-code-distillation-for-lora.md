# claude-code-distillation-for-lora

*Researched: 2026-04-17 13:08 CDT*

# Claude Code Distillation for LoRA Fine-Tuning on DGX Spark

## Overview
Distilling Claude Code's agentic behavior patterns into Qwen3.6-35B-A3B via LoRA on DGX Spark. Uses system prompts (not leaked source code) as instruction templates + synthetic trajectory generation.

## Available Assets (Legal)
1. **Piebald-AI/claude-code-system-prompts** — 110+ prompts, updated per release (v2.1.112). System prompts, sub-agent prompts (Explore, Plan, Verify, Security Monitor), 24 tool descriptions.
2. **claw-code** — Clean-room Python rewrite (75K GitHub stars, DMCA-safe). Provides agentic harness pattern without legal risk.
3. **CheetahClaws** — 174-line agent.py, works with vLLM/Ollama. Zero setup, works on Spark out of box.

## Anti-Distillation Defenses
- **fake_tools**: Decoy tool definitions injected into prompts to poison scraped data
- **CONNECTOR_TEXT**: Buffers reasoning between tool calls, returns signed summaries
- **Bypass**: Both defeatable in ~1hr via MITM proxy or `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` env var
- **Real protection**: Legal, not technical. Clean-room approach (claw-code) is safe.

## 3-Phase LoRA Pipeline

### Phase 1: System Prompt SFT (LEGAL, highest impact)
- Extract 110+ system prompt sections from Piebald-AI repo
- Generate ~500-2000 synthetic SFT examples using Claude API or claw-code
- Format: instruction (system prompt section) + input (task) → output (ideal agent response)
- Teaches Qwen3.6 the BEHAVIOR patterns: tool selection, error recovery, context management, memory architecture
- Key patterns from leak: 3-layer memory (Index→Topic files→Transcripts), verification specialist, security monitor, KAIROS autonomous judgment

### Phase 2: Synthetic Trajectory Generation (LEGAL, medium impact)
- Use Claude API/FriendliAI with Claude Code system prompts as templates
- Feed coding tasks (SWE-bench, HumanEval, Cortex bug database)
- Capture full tool-call trajectories (bypass fake_tools with env var)
- 5K-20K trajectories, ~$50-200 cost

### Phase 3: Self-Play on Spark (FREE, compounding)
- Run CheetahClaws/claw-code against LoRA'd Qwen3.6 on Spark
- Real tasks (Hermes work, SOMA, Anki generation)
- Grade with Cortex heuristic judge → keep good trajectories
- Periodic LoRA updates (weekly) with curated data
- Closes the flywheel: Cortex → LoRA → permanent model improvement (not just tip injection)

## LoRA Technical Specs
| Parameter | Value |
|---|---|
| Base model | Qwen3.6-35B-A3B (35B total, 3B active MoE) |
| LoRA rank | 16-32 |
| LoRA alpha | 32-64 |
| Target modules | q_proj, k_proj, v_proj, o_proj, gate_proj |
| Trainable params | ~50-100M (0.15-0.3%) |
| Batch size | 1-2 (grad accum 8-16) |
| Learning rate | 1e-4 to 5e-5 |
| Dataset size | 2K-20K examples |
| Training time | 2-8 hours on single Spark |
| GPU memory | ~90-100GB BF16 (fits in 128GB with QLoRA) |
| Framework | Unsloth (2-5x faster) or Axolotl |

## Key Architectural Insights from Leak
- **3-Layer Memory**: Index (always loaded, cheap pointers) → Topic files (on demand) → Transcripts (grep only)
- **Tool Loop**: Permission enforcement → Error recovery → Timeout management → Output truncation
- **KAIROS**: Heartbeat → evaluate → act or stay quiet. Separation of initiative from execution.
- **Verification Specialist**: Adversarial sub-agent (PASS/FAIL verdict after build+test+lint)
- **autoDream**: Nightly memory consolidation, compresses to <200 lines/25KB
- **Modular Prompt Architecture**: Cache-aware boundaries for 90% token savings

## What NOT to Do
1. Don't train on raw leaked TypeScript (DMCA risk, wrong format)
2. Don't just copy prompts into context (tip injection already does this, 92% never injected)
3. Don't skip verification (benchmark on testing gym after each LoRA update)
4. MoE LoRA: target shared expert + gate projections, not individual experts

## Compounding Value
Cortex 8,886 nodes → LoRA makes experiences PERMANENT in weights. Not 8 tips injected per turn (92% waste) but actual model capability improvement. Every week = more trajectories → another LoRA update → stronger model.


## Sources

- https://read.engineerscodex.com/p/diving-into-claude-codes-source-code
- https://scortier.substack.com/p/anthropic-forgot-one-line-we-got
- https://github.com/Piebald-AI/claude-code-system-prompts
- https://github.com/SafeRL-Lab/cheetahclaws
- https://www.digitalapplied.com/blog/claude-code-leak-agentic-architecture-lessons-2026
