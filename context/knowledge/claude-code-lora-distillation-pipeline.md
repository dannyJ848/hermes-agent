# Claude Code → Qwen3.6 LoRA Distillation Pipeline

## Dataset
- **Path:** ~/dgx-spark-prep/sft-dataset/claude_code_distill.jsonl
- **Format:** ShareGPT (ChatML template for Qwen3)
- **Size:** 339 examples, ~283K estimated tokens
- **Quality:** 75% of examples have GPT responses >200 chars

## Source Repos (all cloned to ~/dgx-spark-prep/)
1. **codeaashu/claude-code** (leaked source, 386K TS lines, 49MB)
   - Key files: autoDream.ts (325 lines), undercover.ts (90), autoMode.ts (172)
   - memdir/memdir.ts (508 lines) — 3-layer memory architecture
   - coordinator/coordinatorMode.ts — multi-agent coordination
   - tools/shared/spawnMultiAgent.ts — sub-agent spawning
   - services/tools/toolExecution.ts — tool dispatch loop
2. **Piebald-AI/claude-code-system-prompts** (271 prompt files)
   - 37 agent-prompt-* (sub-agents: Explore, Plan, Verify, Security Monitor, Dream)
   - 76 tool-description-* (bash sandbox, git, timeout, dedicated tools)
   - 58 system-prompt-* (behavior, auto-mode, memory, compaction, subagent)
   - 33 data-* (SDK references, managed agents, API docs)
   - 27 skill-* (dream schedule, verify, stuck, dynamic pacing)
   - 39 system-reminder-* (plan mode, token usage, memory, hooks)
3. **CheetahClaws** (174-line agent.py, works with vLLM/Ollama)

## Category Breakdown
| Category | Count | Description |
|---|---|---|
| tool_usage | 76 | Tool dispatch, sandbox, git, bash patterns |
| agent_behavior | 58 | Core behavioral rules, communication style |
| context_management | 40 | Compaction, memory, context injection |
| sub_agent | 37 | Delegation, spawning, worker instructions |
| reference_data | 33 | SDK/API references for tool calling |
| agent_skills | 27 | Slash commands, verify, dream, pacing |
| enriched_* | 36 | High-value prompts converted to multi-turn |
| agentic_pattern | 17 | Extracted from TS decision logic |
| kairos_autonomous | 2 | Heartbeat, autoDream consolidation |
| memory_architecture | 2 | 3-layer retrieval, staleness verification |
| tool_error_recovery | 2 | Standard + sandbox error recovery |
| security/verification/undercover/pacing | 4 | Specialized behavioral patterns |
| agent_trajectory | 3 | Full multi-turn coding examples |

## Converter Scripts
- `distill_claude_code.py` — Base 1:1 converter (271 prompts + 17 TS + 3 trajectories)
- `distill_deep_patterns.py` — Rich synthesized examples (12 deep patterns)
- `spark-lora-train.sh` — Full training + merge pipeline (runs ON Spark)

## LoRA Config
- **Rank:** 16, **Alpha:** 32, **Dropout:** 0.05
- **Target modules:** q_proj, k_proj, v_proj, o_proj, gate_proj (MoE gate!)
- **Precision:** BF16 on Spark (128GB fits with gradient checkpointing)
- **Training:** 3 epochs, LR 5e-5 cosine, warmup 50 steps
- **Time:** ~2-8 hours estimated on single Spark
- **Memory:** ~90-100GB GPU with gradient checkpointing + flash attention

## Post-Training
- Merge LoRA adapter into base model for vLLM serving
- Serve with same BF16 config but merged model
- Evaluate on testing gym baseline (compare LoRA'd vs base)
- Weekly self-play: CheetahClaws on Spark → grade with heuristic judge → add to dataset → retrain

## What Makes This Different From Tip Injection
- **Tip injection:** 8 tips/turn, 92% never injected, same 40 tips win every time
- **LoRA:** Permanent weight changes, no injection bottleneck, every experience baked in
- **Compounding:** Each week of Hermes usage on Spark produces more training data
- **The loop:** Cortex experiences → SFT dataset → LoRA → stronger model → better experiences → repeat
