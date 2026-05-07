======================================================================
HERMES AGENT — COMPLETE CONTEXT SUMMARY FOR NEW CLI
======================================================================
Generated: May 6, 2026 19:35 UTC
Session: Full day of work — tiered memory, LLM judge, checkpoint fixes, training audit

======================================================================
1. REPO STATE
======================================================================
Path: /Users/dannygomez/hermes-agent
Branch: qwen27b-training-artifacts-may3-2026
Commit: ef6f9100a (114 commits ahead of remote)
Remote: dannyJ848/hermes-agent
PAT: [REDACTED — see memory]

======================================================================
2. TRAINING STATUS (CRITICAL)
======================================================================
Model: Qwen3.6-27B-Uncensored + LoRA r=1024
PID: 590094 (DGX Spark 10.0.0.171, user djg6228, pass 6228)
Status: running - healthy since 11:44 AM (7h 50m)

Current: Step 890/4000 (22.3%)
Loss: 2.5775 (CE:2.217 D:1.873 SAE:0.582)
GPU: 85.3GB / 130GB (65.6%, stable)
LR: 1.99e-04 (plateaued after warmup)
Weights: CE=0.96, Distill=0.23, SAE=0.06

Config (VERIFIED — live read in loop):
  max_steps: 4000 (corrected from 10K, stops at 4000)
  save_every: 500 (checkpoint at 1000, 1500, 2000...)
  warmup_steps: 400
  batch_size: 1, grad_accum: 4 (effective batch=4)
  max_seq_len: 512

Timing:
  Step duration: 30.2s (log interval is 10 steps = 302.5s)
  ETA to 4K: ~26 hours (completion ~May 7, 21:00 UTC)

Next checkpoint: Step 1000 (~30 min from now)

======================================================================
3. CHECKPOINT SYSTEM (UNTESTED AT 85GB)
======================================================================
OOM fixes implemented (May 6 restart):
  - CPU-offload save: model.to('cpu') before save
  - empty_cache + synchronize + gc.collect
  - try/finally wrapper (always returns to GPU)
  - save_every reduced 1000→500 for more frequent saves

Watcher: PID 778063 on DGX monitoring step 1000 save
Recovery: /tmp/recovery_plan.sh (auto-finds latest checkpoint)

If training crashes at checkpoint:
  ssh djg6228@10.0.0.171 'bash /tmp/recovery_plan.sh'
  # Prints resume command with latest checkpoint

======================================================================
4. TIERED MEMORY SYSTEM (NEW — May 6)
======================================================================
Files: hermes_cli/subconscious/tiered_memory.py
       hermes_cli/subconscious/memory_daemon.py

Architecture:
  HOT   ~/.hermes/memory.json          2,500 char limit, immediate context
  WARM  ~/.hermes/cerebrum_memory.db   SQLite staging for distilled tips
  COLD  Cortex PostgreSQL / SQLite       Elo-rated archive, vector searchable

Auto-flow:
  1. HOT ≥80% → distill oldest → WARM staging
  2. WARM batch ≥50 → heuristic scoring → quality≥0.6 → COLD (Elo 1200)
  3. COLD Elo>1300 + high access → promote to HOT as "golden rules"
  4. HOT unused 30 days → demote to WARM

Current state:
  HOT: 26.8% (671/2500 chars), 2 entries
  WARM: 3 unrated tips awaiting evaluation
  COLD: fallback SQLite, 0 high-performers

Commands:
  python3 hermes_cli/subconscious/memory_daemon.py --stats
  python3 hermes_cli/subconscious/memory_daemon.py --once --verbose

Skill: tiered-memory-system (meta/)

======================================================================
5. LLM JUDGE (INTEGRATED — May 6)
======================================================================
Model: deepseek-v4-pro
Integration: learning-brain plugin, post_tool_call hook

Flow:
  - Successful tool call with tip output → judge evaluates
  - Score <0.6 → tip + fix go to error_registry
  - Score ≥0.7 + actionable → append to session_continuity.tips_learned

Fixes applied:
  - response_format={"type": "json_object"}
  - max_tokens=2000 (was truncating)
  - JSON extraction from reasoning_content vs content

======================================================================
6. LEARNING-BRAIN PLUGIN (WIRED — May 6)
======================================================================
Path: plugins/learning-brain/
Hooks: pre_tool_call, post_tool_call, on_session_start, on_session_end

State stored in unified_context.db:
  - tool_intelligence (success rates, circuit breaker state)
  - error_registry (pattern → fix mapping)
  - session_continuity (tips_learned, last_action)

Files:
  __init__.py — plugin entry, judge singleton
  context_updater.py — DB updates
  llm_judge.py — DeepSeek evaluation
  instant_context.py — CLI visibility

======================================================================
7. INSTANT CONTEXT SYSTEM
======================================================================
Command: python3 hermes_cli/instant_context.py
Shows: training state, tool intelligence, recent errors, LLM judge,
       tiered memory, active session

Updated with tiered memory bar:
  [TIERED MEMORY]
    HOT   [█████░░░░░░░░░░░░░░░] 26.8% (671/2500)

======================================================================
8. TODAY'S WORK TIMELINE
======================================================================
- Built tiered memory system (hot→warm→cold)
- Integrated LLM judge into learning-brain plugin
- Fixed DeepSeek V4 Pro JSON extraction
- Corrected training config (10K→4K steps, save_every 1000→500)
- Verified max_steps=4000 stops training (live config read)
- Corrected step duration (5min→30s, log interval is 10 steps)
- Deployed checkpoint watcher (PID 778063)
- Created recovery script (/tmp/recovery_plan.sh)
- Updated all persistence layers (DB, memory, master doc, skill)
- Pushed repo: ef6f9100a

======================================================================
9. CRITICAL NOTES FOR NEW CLI
======================================================================
- DGX SSH times out during heavy training — use process_poll, not SSH
- Training runs via nohup (no screen), PID 590094
- First checkpoint at step 1000 — ~30 min, watcher monitoring
- If training dies: run /tmp/recovery_plan.sh on DGX for auto-resume
- max_steps verified: code reads config live, stops at 4000
- Use helpers for cron/patch/skill ops — avoid weak tools directly

======================================================================
10. QUICK COMMANDS
======================================================================
# Full status
python3 hermes_cli/instant_context.py

# Training log (last 5 steps)
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'grep "Step [0-9]*.*Loss" /mnt/bigssd/train_lora_sae_teacher_v1_restart.log | tail -5'

# Process alive check
sshpass -p '6228' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null djg6228@10.0.0.171 'ps -p 590094 -o pid,comm,etime,pcpu,pmem 2>/dev/null || echo "PROCESS_DEAD"'

# Tiered memory stats
python3 hermes_cli/subconscious/memory_daemon.py --stats

# Recovery if crash
ssh djg6228@10.0.0.171 'bash /tmp/recovery_plan.sh'

======================================================================
END OF CONTEXT — New CLI ready to resume
======================================================================
