---
name: reasoning-distillation-pipeline
description: Build a reasoning distillation training pipeline — discover top datasets, normalize formats, mix with generic data at configurable ratios with oversampling and domain weighting.
trigger: When building training data for a model that needs stronger reasoning, when mixing multiple teacher distillation datasets, when preparing SFT data with reasoning traces.
category: mlops/training
---

# Reasoning Distillation Pipeline

Build a mixed training dataset from multiple reasoning distillation sources. Key insight: reasoning traces teach HOW TO THINK, generic data teaches WHAT TO KNOW. You need both.

## Phase 1: Discover Top Datasets

Search HuggingFace for reasoning distillation datasets. Key search terms:
- "reasoning distillation" + model name (GLM-5.1, DeepSeek-R1, Kimi K2.5)
- "chain-of-thought training data"
- "thinking traces dataset"

**Top datasets as of April 2026 (ranked by value):**

Tier 1 (must-have, diverse teachers):
1. `a-m-team/AM-DeepSeek-R1-0528-Distilled` — 2.6M, verified per-category
2. `nvidia/Llama-Nemotron-Post-Training-Dataset` — 3.9M, full SFT+RL
3. `Kassadin88/GLM-5.1-1000000x` — 1M, cleaned: `Jackrong/GLM-5.1-Reasoning-1M-Cleaned`
4. `ianncity/KIMI-K2.5-1000000x` — 1M, cleaned: `Jackrong/Kimi-K2.5-Reasoning-1M-Cleaned`
5. `kai-os/carnice-glm5-hermes-traces` — 1,627 HQ Hermes Agent execution traces (terminal, file, browser, multi-step tool chains with feedback). Subset: sft_messages_high_quality
6. `open-thoughts/OpenThoughts-Agent-v1-SFT` — 15,209 agent traces (nl2bash + InferredBugs). OpenThinker-Agent-v1 (8B) beats Qwen3-32B on agent benchmarks

Tier 1.5 (massive general reasoning — discovered April 2026):
- `glaiveai/reasoning-v1-20m` — 22.2M examples, ~87GB. The single largest open reasoning dataset. Mixed frontier teacher traces across ALL domains. Download priority: highest.

Tier 2 (domain specialists):
5. `nvidia/OpenMathReasoning` — 306K UNIQUE competition math problems, part of NVIDIA's AIMO-2 winning solution
6. `nvidia/OpenCodeReasoning` — 753K competitive coding reasoning traces
7. `FreedomIntelligence/medical-o1-reasoning-SFT` — 90K medical (GPT-4o)
8. `ServiceNow-AI/R1-Distill-SFT` — 1.85M math traces from DeepSeek-R1-Distill-Qwen-32B
9. `PrimeIntellect/NuminaMath-QwQ-CoT-5M` — 5.14M from QwQ-32B
10. `open-r1/codeforces-cots` — 47.8K competitive programming with full CoT reasoning
11. `Nanbeige/ToolMind` — 369K multi-turn tool use conversations (163K synthetic + 205K real)
12. `Crownelius/Opus-4.6-Reasoning-3300x` — 2,160 rows, Claude Opus 4.6 (author-cleaned)
13. `Roman1111111/claude-opus-4.6-10000x` — 9,633 rows, Claude Opus 4.6, $87.20 cost to generate, 27.2M tokens. This is the EXACT dataset used by 97+ distilled models including lordx64, hesamation, r3lax Qwen3.6-35B Claude 4.7 variants. Format: `{"messages": [...], "metadata": {"model", "difficulty", "category"}}`.
14. `Jackrong/Qwen3.5-reasoning-700x` — 633 rows, Qwen3.5-27B full-param, 59.6MB with long CoT up to 239k chars

Tier 3 (high-quality small datasets — oversample these):
- `simplescaling/s1K` — 1K test-time compute traces (Gemini distilled)
- `open-r1/s1K-1.1` — Same 1K problems, DeepSeek-R1 traces (better than Gemini)
- `GAIR/LIMO` — 817 extremely high-quality curated reasoning traces
- `bethgelab/CuratedThoughts` — 222K filtered reasoning traces
- `zwhe99/DeepMath-103K` — 103K deep mathematical reasoning
- `SynthLabsAI/Big-Math-RL-Verified` — 251K RL-verified math
- `Intelligent-Internet/II-Thought-RL-v0` — 342K RL reasoning traces
- `open-r1/OpenR1-Math-220k` — 220K verified math reasoning
- `QuixiAI/dolphin-r1` — 814K mixed reasoning (DeepSeek + Gemini + Dolphin)

Tier 4 (specialized reasoning):
- `kenhktsui/longtalk-cot-v0.1` — 97M tokens, ultra-long CoT
- `open-thoughts/OpenThoughts-114k` — battle-tested, 158K downloads
- `yuchenlin/ZebraLogic` — Logic grid puzzles
- `allenhung1025/causal-arcs` — Causal inference, counterfactuals
- `LEXam-Benchmark/LEXam` — Legal reasoning
- `lm-provers/FineProofs-SFT` — Mathematical proofs
- `ShadenA/MathNet` — Olympiad-level multimodal math

## Phase 2: Normalize Formats

Every dataset has a different format. The unified preprocessor uses a **cascade pattern** — try formats in priority order until one matches.

### Unified standardize_record() Cascade

```python
def standardize_record(record, system_prompt):
    """Convert ANY dataset record to unified message format.
    Returns {"messages": [...]} or None if unhandled."""
    
    # 1. Already has messages list (most common)
    if "messages" in record and isinstance(record["messages"], list):
        messages = record["messages"]
        if messages and messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": system_prompt})
        else:
            messages[0]["content"] = system_prompt
        return {"messages": messages}
    
    # 2. Conversations list (GLM-5.1, Kimi, some Open-R1)
    if "conversations" in record and isinstance(record["conversations"], list):
        messages = record["conversations"]
        if messages and messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": system_prompt})
        else:
            messages[0]["content"] = system_prompt
        return {"messages": messages}
    
    # 3. instruction / output pairs (Alpaca-style)
    if "instruction" in record and "output" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["instruction"]},
            {"role": "assistant", "content": record["output"]}
        ]}
    
    # 4. input / output pairs
    if "input" in record and "output" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["input"]},
            {"role": "assistant", "content": record["output"]}
        ]}
    
    # 5. prompt / completion pairs
    if "prompt" in record and "completion" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["prompt"]},
            {"role": "assistant", "content": record["completion"]}
        ]}
    
    # 6. question / answer pairs
    if "question" in record and "answer" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["question"]},
            {"role": "assistant", "content": record["answer"]}
        ]}
    
    # 7. problem / solution (math datasets)
    if "problem" in record and "solution" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["problem"]},
            {"role": "assistant", "content": record["solution"]}
        ]}
    
    # 8. prompt / generation (code generation datasets)
    if "prompt" in record and "generation" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["prompt"]},
            {"role": "assistant", "content": record["generation"]}
        ]}
    
    # 9. Special: Claude Opus 4.6 format with thinking + solution fields
    if "thinking" in record and "solution" in record:
        assistant_content = record["thinking"] + "\n\n" + record["solution"]
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record.get("problem", record.get("prompt", ""))},
            {"role": "assistant", "content": assistant_content}
        ]}
    
    return None  # Unhandled format
```

### Quality Filtering (Garbage Detection)

After standardization, filter out low-quality records:

```python
def filter_quality(record, min_chars=50, max_chars=64000):
    messages = record.get("messages", [])
    if not messages:
        return False
    
    # Must have assistant response
    assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
    if not assistant_msgs:
        return False
    
    # Length checks
    total_chars = sum(len(m.get("content", "")) for m in messages)
    if total_chars < min_chars or total_chars > max_chars:
        return False
    
    # Refusal/garbage patterns (common in distilled datasets from guarded models)
    garbage = [
        "I'm sorry, but I can't",
        "I cannot assist",
        "I'm not able to",
        "As an AI language model",
        "I don't have the ability",
    ]
    content = assistant_msgs[-1].get("content", "").lower()[:200]
    for pattern in garbage:
        if pattern.lower() in content:
            return False
    
    return True
```

### Chat Template Application

After standardization and filtering, apply the model's chat template:

```python
def apply_chat_template(example, tokenizer):
    messages = example.get("messages", [])
    if not messages:
        return {"text": ""}
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}
```

## Phase 2.5: Phase 1 Sub-Stage Design

For maximum reasoning capability, split foundational training into sub-stages with different data mixes and learning rates:

**Phase 1A: Massive Reasoning SFT (~2-3 days)**
- Objective: Widest possible variety of reasoning patterns
- Data mix: 40% glaiveai/reasoning-v1-20m, 15% OpenMathReasoning, 15% OpenCodeReasoning, 10% AM-DeepSeek, 10% OpenThoughts, 10% others
- LoRA r=128, alpha=256, lr=1e-5, epochs=0.5, max_seq_len=16384
- Target modules: ALL linear layers (q, k, v, o, gate, up, down)

**Phase 1B: Tool Use & Agentic Reasoning (~1 day)**
- Objective: Multi-step tool execution and agent trajectories
- Data: 70% Nanbeige/ToolMind, 20% KodCode, 10% synthetic tool trajectories
- lr=5e-6, epochs=2, max_seq_len=32768 (tool conversations need long context)

**Phase 1C: High-Quality Refinement (~12 hours)**
- Objective: Polish on the absolute best small datasets
- Data: 30% s1K + s1K-1.1, 25% GAIR/LIMO, 20% CuratedThoughts, 15% DeepMath, 10% Big-Math-RL-Verified + Claude Opus 4.6 10K
- lr=5e-6, epochs=3 (slight overfitting on quality data)

**Phase 1D: Causal & Logical Reasoning (~12 hours)**
- Objective: Explicit causal inference and formal logic
- Data: 50% CausalARC, 30% ZebraLogic, 20% LEXam
- lr=5e-6, epochs=2

**Success criteria before proceeding to domain specialization:**
- MATH benchmark >60% (from base ~40%)
- GSM8K >95%
- HumanEval >75%
- BBH >75%
- Can execute 5-step tool use plans without errors

## Phase 3: Mix with Oversampling

Reasoning data is smaller (~100GB) than generic data (318GB+). Without oversampling, reasoning traces get drowned out.

Default ratio: 40% reasoning : 60% generic

Domain weights (higher = more samples selected):
- medical: 3.0 (primary domain bonus)
- agent-terminal: 2.8 (exact use case — shell/file tool calling)
- agent-code: 2.8 (bug-fixing agent traces)
- agent/agent-web/agent-file: 2.5 (multi-step tool chain patterns)
- code: 1.2 (transfers well to general reasoning)
- science: 1.1
- general/math/mixed: 1.0
- instruction_following: 0.8

Teacher weights (diversity bonus for rare teachers):
- Claude-Opus-4.6: 1.4 (proven by 97+ models, Hesamation: +32.86pp MMLU-Pro with 14K samples)
- Kimi-K2.5: 1.3 (different reasoning style)
- LongTalk-CoT: 1.4 (sustained deep reasoning)
- GPT-4o: 1.5 (medical quality)
- Qwen3.5-27B: 1.2 (different teacher arch diversity)
- Others: 1.0-1.2

Long CoT bonus: samples with >2000 char thinking traces get 1.3x weight.

Dedup: hash user messages, prefer reasoning version over generic when both exist (reasoning traces are longer and more valuable).

## Pipeline Ordering: Reasoning BEFORE Domain Specialization

**CRITICAL ARCHITECTURAL PRINCIPLE** (discovered April 2026): For complex domain-specific simulation models, general reasoning capability MUST be distilled BEFORE domain specialization. Skipping this produces plausible-sounding but logically incoherent outputs.

**Correct pipeline order:**
1. **Phase 0:** Infrastructure (EAGLE-3 draft, speculative decode speedup)
2. **Phase 1:** General reasoning distillation (LoRA r=128 on AM-DeepSeek-R1 + OpenThoughts + NuminaMath)
3. **Phase 2:** Domain continued pretraining (health econ, epi, policy corpus)
4. **Phase 3:** Synthetic data generation (domain-specific reasoning chains)
5. **Phase 4:** Instruction SFT on structured formats
6. **Phase 5:** Tool use integration + DPO alignment

**Why this order matters:**
- Reasoning is a FOUNDATIONAL capability (how to think)
- Domain knowledge is APPLICATION layer (what to think about)
- A sharp reasoner with weak domain knowledge learns the domain fast
- A dull reasoner with domain knowledge generates plausible garbage causal chains
- Phase 1 teaches the model HOW to think. Phase 2+ teaches WHAT to think about.

**Example failure mode (health simulation):**
- Without Phase 1: model knows "poverty is associated with diabetes" but generates incoherent causal chains
- With Phase 1: model traces: poverty → food desert → low folate/high sodium diet → 3yr trajectory → homocysteine elevation → endothelial dysfunction → hypertension onset at age 42 → BP 158/96, LVH, 10yr ASCVD risk 14.2%

## Key Research Findings

- Ren et al. 2026 (arXiv:2604.06628): Reasoning SFT shows dip-then-recovery pattern. High-quality long-CoT enables cross-domain transfer. Stronger models learn reasoning structure, not just longer outputs.
- Jackrong proved this works: Qwen3.5-9B/27B trained on GLM-5.1 traces show improved structured reasoning, instruction-following, and latent knowledge activation.
- Kyle Hessling (X: KyleHessling1): GLM-5.1 traces are "incredible" for training — no fake outputs that throw off reasoning.
- Jiunsong (songjunkr) "Super" methodology: abliteration disrupts good behaviors, so Restore SFT (low LR, small LoRA) must run BEFORE generic training.

## File Structure

Three scripts form the pipeline:
1. `superqwen3-reasoning-download.sh` — HF dataset downloads with resume, tier support, manifest
2. `superqwen3-reasoning-normalize.py` — Format normalization to unified chat, per-dataset parsers
3. `superqwen3-reasoning-mix.py` — Weighted sampling, oversampling, dedup, sharded output

## Agent Trace Normalizers (CRITICAL DISTINCTION)

Agent execution traces (Hermes tool calls, terminal commands, browser workflows) are fundamentally different from reasoning traces. They are MULTI-TURN with tool calls interleaved, not simple user/assistant pairs.

**WRONG approach (reasoning normalizer):** Collapse to single user -> assistant pair, extracting thinking + answer. This DESTROYS the tool-calling pattern.

**RIGHT approach (agent trace normalizer):** Preserve the FULL multi-turn conversation including system prompts, user messages, assistant responses with tool calls, tool results, and follow-up responses.

Agent domain weights should be HIGHEST non-medical (2.5-2.8x) because tool-calling patterns are the exact use case. Teacher weight for same-framework traces should be highest (1.6x for GLM-5 Hermes traces on a Hermes-trained model).

## Pitfalls

- **Collapsing agent traces to user/assistant pairs**: These are multi-turn tool-use conversations, not Q&A. The tool call/result/response pattern IS the training signal.
- zstd decompression needed for some HF datasets (AM-DeepSeek uses .zst)
- HF dataset viewer often broken (schema mismatch) — download and parse locally instead
- Some datasets are "research use only" (AM-DeepSeek) — check license
- Thinking tags in Python source code break write_file — use chr() or execute_code
- Large file writes (>10KB) can truncate at token ceiling — use chunked writes or patch()
