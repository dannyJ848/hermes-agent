---
name: super-model-post-abliteration-restoration
version: 1.0.0
description: Post-abliteration restoration pipeline — abliteration degrades 8 quality dimensions (truthfulness, JSON, tool calls, sentinel extraction, identity, loop resistance, unicode, tool integrity). Must run targeted restoration SFT + validation after abliteration before domain training. Based on Jiunsong/songjunkr's SuperGemma4 recipe.
trigger: After running abliteration on any model, when building Super variants, or when post-abliteration quality degrades.
tags: [abliteration, restoration, validation, super-model, quality, post-training]
---

# Super Model: Post-Abliteration Restoration Pipeline

Source: Jiunsong/songjunkr (SuperGemma4-26b-abliterated-multimodal, 66K+ downloads)
Pattern: SuperGemma4 exists, SuperQwen3.6 incoming from same author
HF: huggingface.co/Jiunsong/supergemma4-26b-abliterated-multimodal

## Core Insight

Abliteration removes refusal directions BUT also partially destroys fine-tuned
behaviors. You CANNOT just abliterate and ship — must RESTORE these capabilities
with targeted SFT data after abliteration, before domain-specific training.

## The 8 Degraded Dimensions

1. **False-Premise Correction** — model must correct bad assumptions instead of
   continuing under them. Without restoration: politely agrees with wrong premises.
   Data: (false_premise, correction) pairs.

2. **Exact JSON Output** — raw machine-parseable JSON when requested. Without
   restoration: wraps JSON in markdown/prose. Data: (json_instruction, valid_json) pairs.

3. **Complete Tool-Call Formatting** — full execute_code calls with language AND
   code fields. Without restoration: omits required fields. Data: (tool_scenario,
   complete_tool_call) pairs.

4. **Long-Context Sentinel Extraction** — exact value recovery from long context.
   Without restoration: paraphrases instead of exact extraction. Data:
   (long_context_with_marker, exact_value) pairs.

5. **Identity Consistency** — no role confusion across turns. Without restoration:
   identity drift after abliteration. Data: multi-turn identity-stress conversations.

6. **Loop Resistance** — no repetitive patterns or output loops. Without restoration:
   repetitive outputs especially in long generation. Data: (repetition_trigger,
   diverse_response) pairs.

7. **Unicode/Mixed-Script Handling** — CJK/Korean without glitching. Without
   restoration: hidden-tag leakage, mixed-script artifacts. Data: multilingual
   hygiene pairs.

8. **Tool-Call Integrity** — no fabricated tool names, only available tools.
   Without restoration: invents plausible-sounding tools. Data: (scenario,
   correct_available_tool_call) pairs.

## Updated Training Pipeline

**OLD:** Abliterate -> Domain SFT -> GRPO -> Eval -> Merge
**NEW:** Abliterate -> Restoration SFT -> Domain SFT -> GRPO -> Validate -> Merge

Restoration SFT phase targets ALL 8 dimensions BEFORE domain SFT.
~500-1000 examples per dimension = ~8K total (small but HIGH precision).

## Validation Framework

Run after abliteration AND after each training round. Without this, abliteration
silently degrades quality with no signal.

### Capability Audit (9 tests)
JSON exactness, tool calls, long-context retrieval, hallucination guard, loop
resistance, false-premise correction, identity consistency, unicode handling,
determinism.

### Reliability Audit (20 tests)
Identity (4): role, persona, system prompt adherence, cross-turn consistency
Prompt hygiene (4): no leakage, no injection, no tag escape, no hidden directives
Tool-call integrity (4): format, existence, args, delegation
Long-context (4): retrieval, summarization, continuation, extraction
Unicode (2): CJK, mixed-script
Determinism (2): temperature=0, repeated calls

### Red-Team Suite (13 tests)
Truthfulness (3): false premise, hallucination, fabrication
Leak (2): hidden prompt extraction, system prompt extraction
Loop (2): repetition, pattern lock
Memory (3): injection, extraction, corruption
Tool fabrication (3): invented tools, wrong args, hallucinated API

### SuperGemma4 Results
- Capability: 9/9 (100%)
- Reliability: 20/20 (100%)
- Red-team: 10/13 (remaining 3: 2 safe refusal wording mismatches + 1
  text-only multimodal rejection — NOT quality regressions)

## Stability Refresh Cycle

RE-VALIDATE after every model change. These behaviors REGRESS when you train
on other data. One-time SFT doesn't permanently fix them.

Triggers for re-validation:
- New LoRA merge
- Chat template edit (SYNC chat_template.jinja + tokenizer_config.json)
- Config update
- SFT completion

### April 18 Refresh Example (SuperGemma4)
- Synced chat_template.jinja + inline tokenizer_config.json template
- Hardened false-premise handling
- Tightened JSON-only formatting
- Improved long-context sentinel extraction
- Reinforced identity/prompt-hygiene responses

## Data Synthesis Strategy

Jiunsong's datasets are private (0 public on HF). Synthesize equivalent data:

1. Generate false-premise pairs from medical/textbook data
2. Generate exact-JSON pairs from tool-calling datasets (ToolACE, glaive-v2)
3. Generate sentinel-extraction pairs from long-context samples
4. Generate identity-stress conversations from multi-turn data
5. Generate loop-resistance pairs from repetitive-trigger prompts
6. Generate CJK/unicode hygiene pairs from multilingual data
7. Generate tool-integrity pairs from available tool definitions
8. Generate determinism pairs with temperature=0 seeds

Use the abliterated model itself to generate initial candidates, then filter
for quality. The model's own failure modes tell you what to train on.

## Integration with Spark Pipeline

Add to dual-training-orchestrator.sh as Phase 0.5:
- After: Phase 0 (Abliteration)
- Before: Phase 1 (Domain SFT)
- Data: ~/dgx-spark-prep/training-data/restoration-sft/
- Examples: ~8K high-precision (500-1000 per dimension)
- Time: ~15 min LoRA training on Spark
- Validation: automated audit suite after completion

## Citations

- Jiunsong/supergemma4-26b-abliterated-multimodal (HF, April 18 2026)
- grimjim norm-preserving biprojected abliteration technique
- songjunkr on X/Twitter (SuperQwen3.6 incoming)
