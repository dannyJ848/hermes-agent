# Incident: SSH Intent Loop — May 7, 2026

## What happened
User asked "training status and eta?". I made 6 consecutive SSH calls to spark-85e8.local, each with slightly different arguments, all hunting for the same information (training logs, checkpoint details, max_steps).

## The loop pattern
- Call 1: `ssh ... ps -p 180722 ... nvidia-smi ... ls checkpoints` → got PID alive, GPU 93%, checkpoint step 600
- Call 2: `ssh ... ls outputs, cat *.log, cat training_state.json` → empty (wrong paths)
- Call 3: `ssh ... find ~/qwen_training -type f` → no such dir
- Call 4: `ssh ... ls -la ~ | grep qwen` → found CWD is /data/SpecForge/custom_dflash
- Call 5: `ssh ... ls -lt /data/SpecForge/custom_dflash/checkpoints/` → confirmed step 600 checkpoint
- Call 6: `ssh ... find /data/SpecForge/custom_dflash -name '*.log'` → empty

## Why v1 loop guard would have failed
v1 only checks exact tool name repetition. All 6 calls were `terminal` with `ssh`, so v1 would have flagged call 3 or 4. But the real issue: I had enough data at call 1 (PID alive, GPU 93%, step 600 checkpoint) to answer the user. Calls 2-6 were "just to be sure" hunting.

## Why v2 loop guard catches this
v2 uses **intent hashes**. All 6 calls share the intent "check-training-status" or "find-training-logs". After 3 calls with the same intent, v2 returns exit 1 regardless of exact command variation.

## What I should have done
After call 1: synthesize answer from available data (step 600, ~36 min/100 steps, need max_steps for ETA).
After call 2 (empty): accept that logs aren't in expected place, answer with what I have.
Never make calls 3-6.

## User reaction
User said "loop?" — immediate callout. Zero tolerance. Expected self-detection.

## Fix applied
- Built hermes_loop_guard_v2.py with intent-based detection
- Deployed to /tmp/hermes_loop_guard_v2.py
- Updated skill to reference v2 as primary enforcement
- Added this incident to references/

## Key lesson
**"Same command, different excuse" is still a loop.** If you find yourself running the same tool with a slightly different justification ("let me verify again", "just to be sure", "double-checking"), that's a loop. STOP after the first verification. Record the result and move forward.
