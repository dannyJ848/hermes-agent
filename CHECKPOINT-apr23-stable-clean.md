# Hermes Agent Checkpoint — Apr 23 2026 00:15 UTC
# Label: apr23-stable-clean
# Status: POST-FRANKEN-RECOVERY, tools backed up, session clean

## DGX Spark — BaldEagle Training
- Model: Qwen3.6-27B-Uncensored (dense, BF16)
- Training: 342/600 steps (57%), ~1.9h remaining
- GPU: 95% util, 33GB VRAM, PID 21575 alive
- Metrics: eval_loss 0.9176, top-1 67.7%, top-3 77.0%
- Status file stale ("training_failed") — ignore, training is healthy
- vLLM: port 8000, qwen3.6-27b-uncensored, eager mode

## Tool State
- Franken Monster tools BACKED UP to ~/Desktop/hermes_tools_backup/
- Hermes tools dir nuked and clean
- Custom tools DISABLED pending audit
- 10 tools in backup: enhancement_pipeline.py, qwen36_research_agent.py, enhancement_engine.py, medical_tracker.py, franken_dashboard.py, franken_master.py, research_scanner.py, step1_tracker.py, auto_enhancement.py, medical_anki_generator.py

## Critical Lessons
- apr22-franken-unleashed checkpoint CORRUPTED tool-calling with `:` parameter injection
- Corruption persisted across sessions until tools were removed
- Root cause: unknown, possibly in auto_enhancement.py or franken_master.py
- Recovery: nuke tools dir, restart session, avoid corrupted checkpoint

## Pending Work
- 15 enhancements cataloged (8 applied, 6 pending high-priority)
- Medical domains: psychiatry datasets downloaded, pharmacology/clinical reasoning in research
- OPSD reasoning training wired but not started
- TurboQuant image built (ghcr.io/aeon-7/vllm-dflash:turboquant)

## Next Steps
1. Let BaldEagle training finish (~2h)
2. Audit backed-up tools one-by-one before restoring
3. Rebuild enhancement pipeline from clean base
4. Resume Qwen3.6-27B optimization work
