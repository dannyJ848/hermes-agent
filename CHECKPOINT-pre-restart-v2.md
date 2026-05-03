# Checkpoint: pre-restart-v2
# Created: 2026-04-26
# Purpose: Normal restore checkpoint before fresh Hermes session

## Session Context
- Previous session: 20260425_192231_243827
- Restart reason: Pick up DeepSeek delegation config + fresh context window

## Active Tasks
1. Catalog all datasets on DGX Spark + research discoveries
2. Deep research: cutting-edge Qwen optimization for health data modeling + tool calling
3. Synthesize findings into actionable training pipeline

## DGX Spark Status
- Host: 10.0.0.171 (spark-85e8.local)
- User: djg6228
- Model: Qwen3.6-27B-Uncensored
- vLLM port: 8000
- Served model name: qwen3.6-27b-uncensored
- Docker image: ghcr.io/aeon-7/vllm-dflash:turboquant
- Status: vLLM serving on port 8000, DFlash draft training running
- Disk: 37% full (2.2TB free)

## Hermes Config
- Main provider: kimi-coding (kimi-for-coding)
- Delegation provider: deepseek (deepseek-chat) — NEEDS NEW SESSION TO TAKE EFFECT
- Vision provider: glm-5v-turbo
- Profiles updated: spark-speed, spark-quality, training-gym

## Datasets on Spark (266GB total)
Reasoning: reasoning-v1-20m, openmathreasoning, am-deepseek-r1-distilled, numinamath-qwq-5m, openr1-math-220k, r1-distill-sft, opencodereasoning, codeforces-cots, dolphin-r1, openthoughts2-1m, kodcode-v1-sft-r1, synthetic-1-sft, curatedthoughts, kodcode-v1, ii-thought-rl, deepmath-103k, commitpackft, tulu-3-sft, numinamath-cot, fineproofs-sft, s1k-1.1, s1k, limo
Tool use: toolmind, bfcl
Medical: medical-meadow-cord19, pubmedqa, medmcqa, medical-meadow-flashcards, medqa-usmle, medical-meadow-medqa, medical-meadow-wikidoc, medical-o1-verifiable, raw-medrxiv, pmc-open-access, lexam, mathnet

## Training Status
- DFlash draft: Running on DGX Spark (custom training, phase2_train_draft.py)
- Output: /data/models/Qwen3.6-27B-DFlash-Custom/
- Hidden states: 10000/10000 complete (424GB)
- OPSD: Wired but not started (/data/repos/opsd-training)

## Key Notes
- DeepSeek delegation configured but NEEDS NEW SESSION to take effect
- Hermes v0.11.0 merged (271 commits)
- 5 new tools built and validated
- Unified checkpoint system created (native + context files)
- Native snapshot saved: 20260426-002100-pre-restart

## Resume Command
```
hermes session_restore label="pre-restart-v2"
```
Or start fresh with:
```
hermes chat
```
Then reference this checkpoint file.
