# Hermes Agent Checkpoint — Apr 23 2026 20:45 UTC
# Label: apr23-eagle3-hacking-pause
# Status: EAGLE-3 HACKING PAUSED — BaldEagle trained but incompatible, DFlash available

## DGX Spark — vLLM Status
- Container: STOPPED (qwen36-bf16)
- Last attempt: Eagle-3 speculative decoding with BaldEagle draft model
- Failure: Architecture mismatch — Qwen3.5-based BaldEagle incompatible with Eagle3LlamaForCausalLM
- Error: `AssertionError: Tried to load weights of size torch.Size([5120, 10240]) to a parameter of size torch.Size([5120, 15360])`
- DFlash model READY: `/data/models/Qwen3.5-27B-DFlash/` (5 layers, 5120 hidden, proper DFlash architecture)

## BaldEagle Training — COMPLETE
- Model: Qwen3.6-27B-Uncensored (dense, BF16)
- Training: 600/600 steps, ~4h runtime
- Model saved: `/data/baldeagle-outputs/qwen36-27b-draft/`
- Size: 3.87GB (1.67B params)
- Status: TRAINED BUT NOT INTEGRATED (vLLM Eagle-3 architecture incompatibility)

## Hermes State
- Tools: 5 safe enhancement tools restored (enhancement_engine, medical_tracker, research_scanner, step1_tracker, medical_anki_generator)
- Research DB: 17 enhancements cataloged, 9 applied, 8 pending
- SOUL.md: Restored to ~/.hermes/SOUL.md
- Workspace checkpoints: 775 historical checkpoints copied
- State.db: Surgically cleaned (145,744 messages, 8,483 sessions)
- Catch-net: ACTIVE (REVERT_STATE_DB.sh ready)

## Critical Lessons from Eagle-3 Hacking
1. vLLM Eagle-3 requires exact architecture match — can't use Llama class for Qwen weights
2. Registry patching alone insufficient — SpeculativeConfig validation hardcodes supported architectures
3. Weight loading patches (KeyError skip) work but dimension mismatch is fatal
4. Syntax errors in patches (broken f-strings) can crash the entire vLLM startup
5. DFlash is the proven working speculative method for Qwen3.6 on GB10

## Pending Speed Optimization Paths
1. **DFlash** — Immediate restart with Qwen3.5-27B-DFlash model (~40 tok/s proven)
2. **MTP** — Native Qwen3.6 MTP heads (deadlocks with --enforce-eager, lockups with torch.compile)
3. **Custom Eagle-3 class** — Build Eagle3Qwen3_5ForCausalLM from scratch (very complex)
4. **TileKernels** — DeepSeek's new GPU kernel DSL (research needed)
5. **LongSpec** — LSTM-based context-agnostic drafting (research needed)
6. **--language-model-only** + **--performance-mode throughput** — vLLM recipe flags (untested)

## Medical Domain Progress
- Psychiatry datasets downloaded
- Pharmacology/clinical reasoning in research phase
- Step 1 tracking active
- Anki generator ready

## Next Steps (when resuming)
1. Restart vLLM with DFlash for immediate usable speedup
2. Continue deep research on alternative speed methods
3. Consider rebuilding BaldEagle with proper DFlash architecture instead of Eagle-3
4. Benchmark all configurations and document speed/quality tradeoffs

## Files Modified/Created
- `/data/models/eagle3-draft-qwen36/` — BaldEagle draft (trained but unused)
- `/data/models/baldeagle-draft/` — Alternative draft location
- `/data/tmp/llama_eagle3_patched.py` — vLLM patch (weight loading fix)
- `/data/tmp/registry_patched2.py` — vLLM patch (inspection bypass)
- `~/.hermes/REVERT_STATE_DB.sh` — Emergency revert script
- `~/.hermes/scripts/state_db_merge.py` — DB merge tool
- `~/.hermes/CHECKPOINT-apr23-stable-clean.md` — Pre-hacking clean state
