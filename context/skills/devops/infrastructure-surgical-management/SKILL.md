---
title: Infrastructure Surgical Management
description: Kill-first, selective-re-enable approach to managing infrastructure processes, jobs, and services. For users who want immediate action without review or explanation.
name: infrastructure-surgical-management
trigger: When managing cron jobs, training processes, background daemons, or any infrastructure where the user wants everything stopped immediately before selective restart.
---

# Infrastructure Surgical Management

## User Preference (Embedded)

**This skill encodes a user preference discovered May 3, 2026:**

> "When they see 42 cron jobs, they want them all dead immediately — no review, no nuance. Action-oriented, short commands, impatient with explanations or preamble."

**ADDITIONAL preference discovered May 17, 2026 — Systemd daemons explicitly rejected:**

> "eliminate any daemon, I don't want it depending on any daemon. it should be able to go autonomous with tool calling, etc for the whole night."

User wants persistent autonomous agents that survive overnight WITHOUT systemd dependency. Use **screen/tmux sessions only** for background processes. Never create systemd unit files, systemctl services, or any daemon infrastructure.

When the user says things like:
- "kill everything"
- "stop all of them"
- "I don't want to review, just kill"
- "why are you explaining, just do it"
- "short commands only"
- "no daemon" / "eliminate any daemon"
- "go autonomous"

**DO NOT:**
- List processes before killing
- Ask for confirmation on each item
- Explain what you're about to do
- Show previews or dry-runs
- Use verbose output
- Create systemd services or unit files
- Use `systemctl`, `service`, or daemon management
- Depend on systemd for process persistence

**DO:**
- Kill everything matching the pattern immediately
- Use short, direct commands
- Report what was killed after the fact (not before)
- Let the user ask for details if they want them
- Use `screen -dmS <name>` for persistent background processes
- Use `tmux new-session -d -s <name>` as alternative
- Verify with `screen -ls` or `tmux ls`

## Pattern: Kill-First Recovery

```bash
# 1. Kill everything matching pattern (no preview, no confirmation)
pkill -9 -f 'train_'
pkill -9 -f 'python.*train'

# 2. Verify nothing remains (quick check)
ps aux | grep -E 'train_|python.*train' | grep -v grep || echo "CLEAN"

# 3. Only if user asks: selectively restart what they want
# Wait for user instruction before restarting anything
```

## Pattern: Cron Job Massacre

```bash
# User sees 42 cron jobs and wants them dead
# DON'T list them first
# DON'T ask which ones to keep

# JUST KILL
hermes cron stop-all
# or
pkill -f 'hermes.*cron'

# Report after: "All cron jobs stopped. 0 running."
# Let user say "start X" if they want something back
```

### Pattern: System Recovery After Freeze

When a system (like DGX Spark) becomes unresponsive:

```bash
# DON'T diagnose why it froze
# DON'T check logs first
# DON'T attempt graceful shutdown

# JUST REBOOT (if physical access) or wait for it to die
# Report: "System was frozen. Rebooted. Fresh state."
```

### Pattern: DGX Cycling (User Recovery Method)

When DGX Spark becomes unresponsive under training load:

**User action:** Power cycle the DGX (physical button or remote power management).

**What this means in user communication:**
- "it ready" = DGX is responsive after cycling, ready for commands
- "okay just cycled it" = DGX was power-cycled, fresh state, SSH should work
- Short phrases, no explanation needed

**Post-cycle protocol:**
1. Verify SSH: `ssh -o ConnectTimeout=10 djg6228@10.0.0.171 'echo alive'`
2. Kill any orphaned processes from before cycle: `pkill -9 -f 'train_'`
3. Clear GPU: `python3 -c "import torch; torch.cuda.empty_cache()"`
4. Check for auto-resume scripts that may respawn duplicates
5. Launch fresh training instance

**Why cycling works:**
- SIGKILL from SSH doesn't work when system is completely frozen
- GPU memory remains allocated even after process death (driver state)
- Only full power cycle clears GPU and resets driver state
- Cycling is faster than waiting for OOM killer or network recovery

**See:** `references/dgx-training-double-launch-may8-2026.md` for post-cycle duplication hazard

## Anti-Patterns to Avoid

| What NOT to do | What the user wants |
|----------------|---------------------|
| "Here are the 42 cron jobs, which ones should I kill?" | "Kill all 42. Now." |
| "Let me check what each process is doing first..." | "pkill -9. Done." |
| "Before I stop this, let me explain why it might be important..." | "Stop it. I'll tell you if I need it." |
| "Would you like me to save state before killing?" | "Kill. If I cared about state I'd have said." |
| Long command output with headers and footers | Short status: "Killed 42. Clean." |

## Training Process Management

```bash
# Kill all training attempts (the user wants this often)
pkill -9 -f 'train_'
pkill -9 -f 'python3.*train'
pkill -9 -f 'deepspeed'
pkill -9 -f 'torchrun'

# Quick verify
ps aux | grep -E 'train_|deepspeed|torchrun' | grep -v grep | wc -l
# Expected: 0
```

## SSH Session Cleanup

```bash
# When SSH hangs due to overloaded system:
# DON'T wait for timeout
# DON'T try graceful disconnect

# JUST kill the local SSH process
kill -9 $(pgrep -f 'ssh.*10.0.0.171')
# Then try fresh connection after system recovers
```

## Verification Style

When user asks for status AFTER killing:

```bash
# GOOD (short):
ps aux | grep train | grep -v grep | wc -l
# Output: 0

# BAD (verbose):
echo "Checking for remaining training processes..."
for proc in $(ps aux | grep train | grep -v grep | awk '{print $2}'); do
    echo "Found process $proc"
done
echo "Verification complete. No training processes found."
```

## Loop Guard Integration

When monitoring long-running training:

```bash
# DON'T poll repeatedly with explanations
# Max 2 checks, then stop or escalate

# Check 1: tail -n 5 log
# Check 2: ps aux | grep train
# After 2 checks: either fix or let it run
```

**CRITICAL: Use intent-based loop guard v2, not v1.**
v1 only catches exact tool-name repetition. v2 catches "same command, different excuse" loops where you vary the arguments slightly but keep the same goal.

**Deploy and use:**
```bash
# Already deployed at /tmp/hermes_loop_guard_v2.py
# Before EVERY tool call:
python3 /tmp/hermes_loop_guard_v2.py terminal "check-training-status" 2>/dev/null || { echo "LOOP BLOCKED"; exit 1; }
```

**Intent naming convention:** Use short, descriptive intent strings:
- `ssh-check-training-status` — checking if training is alive
- `ssh-find-training-logs` — hunting for log files
- `ssh-check-gpu-memory` — checking GPU utilization
- `git-commit-changes` — committing code
- `verify-checkpoint-integrity` — checking if checkpoint is valid

**Rule: 3 strikes by intent = STOP.** After 3 calls with the same intent, you MUST synthesize what you have or escalate. No "just one more check."

**May 7, 2026 incident:** 6 SSH calls to spark-85e8.local, each with different grep/ls/find arguments, all hunting for training status. v1 would not catch this (different commands). v2 catches it at call 3 because the intent "find-training-logs" or "check-training-status" is the same. See `references/ssh-intent-loop-may-07-2026.md`.

## Auto-Cleanup for Stuck Background Processes

Pattern for daemons that spawn work cycles (flywheel, training, evals):

```python
# Add to any daemon that creates database-backed work cycles:

def cleanup_stuck_cycles(max_age_minutes=30):
    """Kill cycles stuck running longer than threshold."""
    try:
        import psycopg2  # or sqlite3
        conn = psycopg2.connect(dbname='cortex', ...)
        cur = conn.cursor()
        cur.execute(
            "UPDATE flywheel_cycles SET status = 'killed' "
            "WHERE status = 'running' AND started_at < NOW() - INTERVAL '%s minutes'",
            (max_age_minutes,)
        )
        killed = cur.rowcount
        conn.commit()
        if killed > 0:
            print(f"[Cleanup] Killed {killed} stuck cycles")
    except Exception as e:
        print(f"[Cleanup] Error: {e}")

# Run every N ticks in the daemon main loop:
tick_count += 1
if tick_count >= 10:  # every 10 minutes
    cleanup_stuck_cycles()
    tick_count = 0
```

**Why this matters:** Background daemons that call external APIs (DeepSeek, OpenAI) will accumulate zombie cycles when API calls timeout or DB locks occur. Without cleanup, the "running" count grows indefinitely and the system appears broken.

**Rule of thumb:** Any daemon that inserts a "running" row into a database must also have a cleanup routine that kills rows older than 2× the expected completion time.

## Session Checkpointing Pattern

When the user says "save everything" or "checkpoint":

```bash
# 1. Git commit all code changes
git add -A && git commit -m "Checkpoint: <brief description>"

# 2. Save memory entries (already automatic via memory tool)

# 3. Write checkpoint file for cross-session resume:
cat > ~/.hermes/CHECKPOINT-$(date +%b%d)-<topic>.md << 'EOF'
## Resume Point
- Commit: <hash>
- Status: <what was running>
- Next step: <what to do next>
- Key files: <list>
EOF

# 4. Report: "Checkpoint <hash>. Everything saved."
```

**DON'T:** Explain what a checkpoint is, ask what to include, or show a preview.
**DO:** Just do it and report the commit hash.

See `references/surgical-precision-session-feedback.md` for the original feedback that shaped this skill.

## DGX Hermes Process Topology

When managing Hermes instances on DGX Spark, there are **TWO distinct process types** that must NOT be confused:

| Process Type | Command | Purpose | Kill? |
|-------------|---------|---------|-------|
| **Systemd service** | `run_hermes_fixed.py` | Background persistent agent (auto-restart) | **NO** — This is the production instance |
| **Foreground CLI** | `venv/bin/hermes` | Interactive session the user is actively using | **NO** — This is what the user is talking to |

**Critical pitfall:** The foreground CLI process (e.g., PID 98044 running `venv/bin/hermes` in pts/0) may appear "old" or "duplicate" because the systemd service is also running. But the foreground process is the ONE the user is actively interacting with. Killing it disconnects the user.

**Before killing ANY Hermes process on DGX:**
```bash
# 1. Identify ALL Hermes processes
ps aux | grep -E "hermes|run_agent" | grep -v grep

# 2. Check which one is the foreground (has tty)
ps aux | grep hermes | grep -v grep | awk '{print $2, $7, $11}'
# pts/0 = foreground CLI (DON'T KILL)
# ?     = background service (OK to restart if needed)

# 3. Check systemd status
systemctl --user status hermes-agent.service

# 4. Only kill if explicitly confirmed as duplicate/old
# AND the user is not actively using it
```

**If you accidentally killed the foreground instance:**
```bash
# The user needs to reconnect. The systemd service is still running.
# Tell them: "The background service is still running. Please reconnect."
# DO NOT restart the service unless asked.
```

**Verification pattern:**
```bash
# Check if merged-lora is responding (POST, not GET)
curl -s --max-time 30 -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "merged-lora", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}'
# 404 on GET /v1/models/merged-lora is NORMAL — use POST for chat completions
```

## DGX Training Process Management

When training large models (27B+) on DGX Spark:
- **SSH will become unresponsive during training** — This is EXPECTED, not a system failure. The DGX prioritizes training computation over network I/O. Do NOT panic-kill processes when SSH times out.
- **Use process_poll instead of SSH during heavy loads** — `process_poll` queries the background process directly without SSH overhead. Use this for status checks when training is active.
- **Wait for training to complete or for the system to become responsive again** — SSH timeouts resolve automatically when GPU load decreases.
- Use background processes with log files
- Verify dataset paths exist (actual paths differ from expected)
- Handle parquet format with numpy array conversion
- **CRITICAL**: Qwen3.5 gradient checkpointing — OLD bug with `use_reentrant=True` caused deadlock. NEW fix: `use_reentrant=False` works stably. See `references/dgx-training-process-management.md` for full details
- **CRITICAL**: Full fine-tuning 27B needs 271GB memory (model + grads + AdamW) — impossible on 130GB GPU
- **CRITICAL**: Checkpoint saves are OOM hazards at memory edge. When GPU utilization >65%, `save_pretrained()` needs extra memory to serialize weights. This pushes total usage over capacity → SIGKILL. See `references/dgx-training-oom-fix-may6-2026.md` for the 4-phase CPU offload fix.
- **CRITICAL**: Resume from checkpoint requires correct PeftModel API — `model.from_pretrained(ckpt_path)` is WRONG. Use `PeftModel.from_pretrained(model, ckpt_path)` or `model.load_adapter(ckpt_path, adapter_name='default')`. See `references/dgx-training-resume-bug-may6-2026.md` for full details.
**CRITICAL: When training crashes and auto-resume scripts exist, they may launch DUPLICATE processes on reboot. Always verify process count before declaring success: `ps aux | grep train_ | grep -v grep | wc -l` must return 1. If >1, kill all and relaunch manually. See `references/dgx-training-double-launch-may8-2026.md` for the May 8 incident.**

**CRITICAL: PyTorch 2.6+ `weights_only` default breaks checkpoint resume.** `torch.load()` default changed from `weights_only=False` to `weights_only=True`. Optimizer state files with custom classes fail with `pickle.UnpicklingError`. Fix: add `weights_only=False` to all `torch.load()` calls. See `references/pytorch-2.6-weights-only-breaks-resume-may8-2026.md` in qwen27b-training-pipeline skill.
- See `references/dgx-training-process-management.md` for full details including memory budget math, all failure modes, and what actually works

### Training Death Diagnosis (May 6, 2026)

When training appears to have stopped:

```bash
# 1. Check if process exists (quick, no explanation)
sshpass -p '6228' ssh -o ConnectTimeout=10 djg6228@10.0.0.171 'ps -p <PID> -o pid,comm 2>/dev/null || echo DEAD'

# 2. Check last logged step (not just last log line)
sshpass -p '6228' ssh -o ConnectTimeout=10 djg6228@10.0.0.171 'grep "Step [0-9]*.*Loss" /mnt/bigssd/train.log | tail -1'

# 3. Check log file size vs expected
current_lines=$(sshpass ... 'wc -l < /mnt/bigssd/train.log')
expected_lines=$((step_number * ~40))  # rough heuristic

# 4. Check for truncated writes (partial lines at EOF)
tail -1 /mnt/bigssd/train.log | grep -q "^\[" || echo "TRUNCATED_WRITE"

# 5. Check checkpoint integrity (not just existence)
ls -la checkpoints/checkpoint_step_500/
# If only README.md exists and no .bin/.pt files → checkpoint save FAILED
```

**Common failure modes:**
| Symptom | Likely cause | Action |
|---------|-------------|--------|
| Process dead, no OOM in dmesg | OOM during checkpoint save (save_pretrained needs extra memory) | Restart with `save_every` doubled |
| Log ends with partial line | Process killed mid-write (SIGKILL, not SIGTERM) | Check system memory pressure |
| Checkpoint dir exists but empty | save_pretrained started but didn't finish | Restart from scratch or earlier checkpoint |
| GPU shows [N/A] in nvidia-smi | GPU driver crashed or process holding GPU died | Reboot DGX |
| Last step ~500, 1000, 1500 | save_every boundary — OOM during save | Increase save_every or reduce grad_accum |
| Resume fails with TypeError | `model.from_pretrained()` missing arg | Use `PeftModel.from_pretrained(model, path)` |

**Restart strategy when no valid checkpoint exists:**
1. Kill any remaining python processes (they may be zombie/hung)
2. Clear GPU memory: `nvidia-smi` and check for hung processes
3. Restart with modified config:
   - `save_every = 1000` (was 500) — fewer saves = fewer OOM opportunities
   - Consider `grad_accum_steps = 2` (was 4) — less memory pressure during backward
   - Or keep grad_accum=4 but monitor memory during saves
4. Accept step loss — 490 steps = ~4 hours, not catastrophic

**Key insight from May 6 session:** `model.save_pretrained()` at step 500 triggered OOM because:
- Training uses 85.5GB/130GB continuously
- save_pretrained needs additional memory to serialize 5.1B LoRA weights
- Combined usage exceeds 130GB → OOM killer terminates process
- Checkpoint directory is created but weights never written → empty checkpoint

**Fix:** Either increase save interval (less frequent) or reduce batch/grad_accum (more headroom for saves).

**Better fix (applied May 6, 11:40 UTC):** Four-phase CPU offload save:
1. `empty_cache()` + `gc.collect()` + `synchronize()`
2. `model.to('cpu')` — free GPU memory
3. Save on CPU (no GPU pressure)
4. `model.to('cuda')` — return to GPU

Plus try/except/finally to ensure GPU return even on failure.
Plus auto-resume logic that validates checkpoint integrity (checks for weight files, not just directory existence).

**REVISED FIX (applied May 6, 20:30 UTC):** The four-phase CPU offload still failed at step 1000. `model.to('cpu')` on 85GB model exceeded 121GB system RAM. The kernel OOM killer killed the process silently.

**Final fix (Save — Fix #1):** Save only LoRA adapter parameters (small tensors) instead of moving the full model:
```python
lora_state = {}
for name, param in model.named_parameters():
    if param.requires_grad:
        lora_state[name] = param.detach().cpu()
torch.save(lora_state, os.path.join(path, "adapter_model.bin"))
```

**Final fix (Resume — Fix #2):** Correct PeftModel API for loading adapters:
```python
# WRONG — fails with TypeError: missing required positional argument 'model_id'
model = model.from_pretrained(ckpt_path)

# CORRECT — pass base model as first argument
if hasattr(model, 'load_adapter'):
    model.load_adapter(ckpt_path, adapter_name='default')
else:
    model = PeftModel.from_pretrained(model, ckpt_path)
```

**Why this works:** LoRA params are ~100MB-1GB, not 85GB. No full model CPU allocation. System RAM stays safe. The `param.detach().cpu()` copies individual small tensors, not the whole model graph. On resume, reload base model from HuggingFace cache and apply saved adapters.

**See:** `references/may6-2026-training-crash-diagnosis-pattern.md` for full session log and diagnosis steps.
**See:** `references/dgx-training-resume-bug-may6-2026.md` for resume bug reproduction and fix.

## Learning Apparatus Maintenance

When the user asks to audit or fix learning infrastructure (cortex daemon, training gym, distillation pipeline, skills, ELO system):

**DO:**
1. Check actual database files — `cortex.db`, `cerebrum_memory.db`, `distilled_tips.db`
2. Check if processes are alive vs DB is empty (0 bytes = dead even if PID exists)
3. Kill stuck processes before rebuilding
4. Use `--theirs` for cherry-pick conflicts when no custom changes exist
5. Rebuild from the operational system (cerebrum → cortex sync)
6. Fix broken skills by adding `SKILL.md` index files to category directories
7. Verify with `git status --short` and `git diff HEAD -- <file>`

**DON'T:**
- Assume a running process means a working database
- Try to patch with `skill_manage` when `write_file` + `execute_code` are proven
- Leave 0-byte databases in place
- Accept "no such table" errors without checking if the table exists in a different DB

**Pattern: Kill-Stuck-Rebuild**
```bash
# 1. Find and kill stuck processes
pgrep -f 'cortex_daemon' | xargs kill -9

# 2. Remove corrupted DB
rm /Users/dannygomez/.hermes/cortex.db

# 3. Rebuild from operational source
# (cerebrum_memory.db has the data — sync top N tips to new cortex.db)

# 4. Verify
sqlite3 /Users/dannygomez/.hermes/cortex.db "SELECT COUNT(*) FROM cortex_nodes"
```

**Pattern: Skill Category Fix**
```bash
# When skill_view reports broken skills (missing SKILL.md in category dirs):
for cat in apple research gaming devops; do
    cat ~/.hermes/skills/$cat/SKILL.md << 'EOF'
---
title: $(echo $cat | tr '-' ' ' | titlecase) Skills
description: Skill category index
---
# $(echo $cat | tr '-' ' ' | titlecase) Skills
EOF
done
```

## Learning Apparatus Maintenance

When the user asks to audit or fix learning infrastructure (cortex daemon, training gym, distillation pipeline, skills, ELO system):

**DO:**
1. Check actual database files — `cortex.db`, `cerebrum_memory.db`, `distilled_tips.db`
2. Check if processes are alive vs DB is empty (0 bytes = dead even if PID exists)
3. Kill stuck processes before rebuilding
4. Use `--theirs` for cherry-pick conflicts when no custom changes exist
5. Rebuild from the operational system (cerebrum → cortex sync)
6. Fix broken skills by adding `SKILL.md` index files to category directories
7. Verify with `git status --short` and `git diff HEAD -- <file>`
8. **Always inspect schema before querying** — `PRAGMA table_info(table_name)` before `SELECT` to avoid `no such column` errors
9. **Use `write_file` + `execute_code` instead of weak tools** — `skill_manage` (49% success), `patch` (59% success), `cronjob` (13% success) are unreliable. Write scripts directly and execute them.

**DON'T:**
- Assume a running process means a working database
- Try to patch with `skill_manage` when `write_file` + `execute_code` are proven
- Leave 0-byte databases in place
- Accept "no such table" errors without checking if the table exists in a different DB
- Blindly query columns without checking schema first
- Trust `skill_manage` for complex operations — it fails half the time

**Pattern: Inspect-Before-Query**
```python
# ALWAYS inspect schema before querying
conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
c = conn.cursor()
c.execute("PRAGMA table_info(distilled_tips)")
columns = [r[1] for r in c.fetchall()]
print(f"Columns: {columns}")  # ['id', 'tip_type', 'condition', ...]

# Then build query using actual columns
if 'elo' in columns:
    c.execute("SELECT AVG(elo) FROM distilled_tips")
else:
    print("No elo column — skip ELO analysis")
```

**Pattern: Kill-Stuck-Rebuild**
```bash
# 1. Find and kill stuck processes
pgrep -f 'cortex_daemon' | xargs kill -9

# 2. Remove corrupted DB
rm /Users/dannygomez/.hermes/cortex.db

# 3. Rebuild from operational source
# (cerebrum_memory.db has the data — sync top N tips to new cortex.db)

# 4. Verify
sqlite3 /Users/dannygomez/.hermes/cortex.db "SELECT COUNT(*) FROM cortex_nodes"
```

**Pattern: Skill Category Fix**
```bash
# When skill_view reports broken skills (missing SKILL.md in category dirs):
for cat in apple research gaming devops; do
    cat ~/.hermes/skills/$cat/SKILL.md << 'EOF'
---
title: $(echo $cat | tr '-' ' ' | titlecase) Skills
description: Skill category index
---
# $(echo $cat | tr '-' ' ' | titlecase) Skills
EOF
done
```

**Pattern: Weak Tool Workaround**
```python
# Instead of skill_manage (49% success), patch (59% success), cronjob (13% success):
# Use write_file to create scripts, then execute_code to run them.
# This is the proven path: write_file(87%), execute_code(92%).

# Example: Instead of using patch tool for complex multi-file changes:
# 1. Write a Python script that makes all changes
# 2. execute_code to run it
# 3. Verify with terminal commands

# Example: Instead of skill_manage to update a skill:
# 1. Read the skill with skill_view
# 2. Write the updated content with write_file
# 3. Verify the file exists
```

**Pattern: Terminal String Interpolation Gotcha**
```bash
# NEVER pass complex Python code directly to terminal command
# Bash interpolates $variables, \n, and quotes — destroys the script

# BAD:
terminal(command="""python3 -c "import sys; print('hello')"""")

# GOOD:
# 1. Write script to file with write_file
# 2. Run with terminal: python3 /path/to/script.py

# Example:
write_file(path="/tmp/test_script.py", content="import sys; print('hello')")
terminal(command="python3 /tmp/test_script.py")
```

**Why this matters:** In this session, multiple terminal calls failed with `bad substitution` because bash tried to interpolate Python strings containing `$`, `\n`, and `"`. The fix is always: write_file first, then execute.

**Pattern: SSH Remote Script Execution (Avoid Hermedoc Hell)**
```python
# NEVER pass multi-line scripts via SSH heredocs — shell escaping destroys them
# 4 consecutive failures observed May 15, 2026 trying to pass SQL/Python via SSH

# BAD (fails with SyntaxError, bad substitution, or truncated output):
ssh user@host 'python3 << "EOF"\nimport sqlite3\n...\nEOF'

# GOOD (proven path — write locally, pipe via stdin, execute remotely):
import subprocess

script_content = '''
import sqlite3
# ... complex script ...
'''

result = subprocess.run(
    ['ssh', '-i', key_path, 'user@host', 'cat > /tmp/script.py && python3 /tmp/script.py'],
    input=script_content,
    capture_output=True,
    text=True,
    timeout=30
)
# write_file (87% success) + subprocess.run (92% success) = proven path
```

**Why this matters:** Bash heredocs inside SSH commands fail because:
1. The local shell interpolates `$variables` before SSH sees them
2. Quote nesting (`"` inside `'`) breaks at 2+ levels deep
3. Backslash escaping (`\n`, `\\`) gets stripped by intermediate shells
4. Triple-quoted Python strings contain newlines that bash treats as command terminators

**The only reliable pattern for complex remote scripts:**
1. `write_file` to create script content locally (or use `execute_code` to build it)
2. `subprocess.run` with SSH to pipe content to remote file + execute
3. Never use `terminal(command="ssh ... << EOF")` for multi-line scripts

## Unified Tree Management

When the user asks to merge separate systems into a central tree or "see everything at once":

**DO:**
1. Create symlinks from the central tree to the actual files (don't copy — keep single source of truth)
2. Create a `systems_registry.json` that lists all components with their paths and status
3. Create a unified status script that queries all systems and reports in one view
4. Add persistence layer tracking to the registry (DB paths, sizes, last backup)
5. Create health checkers that handle missing tables gracefully (inspect schema before querying)
6. **Search broadly first** — check `~/subconscious/`, `~/custom_dflash/`, `~/.hermes/` before concluding something doesn't exist
7. **Create unified context database** — `~/.hermes/unified_context.db` with tables for tool intelligence, errors, session continuity, and critical state
8. **Create instant context viewer** — `python3 hermes_cli/instant_context.py` shows everything a new CLI needs
9. **Create context updater** — `hermes_cli/context_updater.py` for live updates during sessions

**DON'T:**
- Copy files into the central tree (creates divergence)
- Leave systems invisible to the central tree
- Create health checkers that crash on missing tables
- Forget to update the registry when adding new components
- **Narrow search scope** — don't search only `hermes_cli/` when the user says "find it"
- Leave context scattered across multiple DBs and files

**Pattern: Broad Search First**
```bash
# When user says "find it" and initial search fails:
# 1. Search hermes_cli/ (fast, likely location)
# 2. Search gateway/ (if gateway-related)
# 3. Search ~/subconscious/ (training apparatus, 2653 files)
# 4. Search ~/custom_dflash/ (training scripts)
# 5. Search ~/.hermes/ (config, checkpoints, skills)
# 6. Search entire home directory (last resort)
```

**Pattern: Symlink Integration**
```bash
# Create central tree with symlinks
mkdir -p hermes_cli/subconscious/{judge,flywheel,eval}
ln -s /Users/dannygomez/subconscious/llm_judge.py hermes_cli/subconscious/llm_judge.py
ln -s /Users/dannygomez/subconscious/cortex_flywheel.py hermes_cli/subconscious/cortex_flywheel.py
```

**Pattern: Registry-Driven Status**
```python
# Load registry and report all systems
with open('hermes_cli/systems_registry.json') as f:
    registry = json.load(f)

for system, info in registry.items():
    print(f"[{system}] Status: {info['status']}")
    # Query each system's actual state
```

**Pattern: Defensive Health Checker**
```python
# Check table existence before querying
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cortex_nodes'")
if c.fetchone():
    c.execute("SELECT COUNT(*) FROM cortex_nodes")
    count = c.fetchone()[0]
else:
    count = 0  # Table doesn't exist yet
```

**Pattern: Unified Context System**
```python
# Create unified context database for instant CLI handoff
conn = sqlite3.connect('/Users/dannygomez/.hermes/unified_context.db')
c = conn.cursor()

# Tables: cli_context, tool_intelligence_snapshot, session_continuity, error_registry
c.execute('''
    CREATE TABLE IF NOT EXISTS cli_context (
        key TEXT PRIMARY KEY,
        category TEXT,
        value TEXT,
        priority INTEGER DEFAULT 5,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Seed with critical state
c.execute('''
    INSERT OR REPLACE INTO cli_context (key, category, value, priority)
    VALUES ('training_pid', 'training', '590094', 1)
''')
```

**Pattern: Instant Context Viewer**
```bash
# New CLI session startup command
python3 hermes_cli/instant_context.py

# Shows:
# [CRITICAL] Training PID, branch, judge status
# [TOOL INTELLIGENCE] All tools with circuit states
# [RECENT ERRORS] Patterns + fixes
# [ACTIVE SESSION] Tasks, decisions, files modified
```

**Pattern: Live Context Updates**
```python
from hermes_cli.context_updater import ContextUpdater
updater = ContextUpdater()
updater.update_tool_result('write_file', success=True, latency_ms=150)
updater.record_error('patch', 'identical strings', 'Use write_file instead')
updater.update_session('session_id', task='new task', decision='use X over Y')
updater.set_context('new_key', 'new_value', priority=1)
```

## Git Divergence Handling

When a fork has massively diverged from upstream (no merge base, thousands of conflicting files):

**DON'T:**
- Attempt a standard merge or rebase — it will fail with "no merge base"
- Cherry-pick blindly — every commit will conflict because the file histories diverged
- Try to resolve 2,946 file conflicts manually
- Apply changes that risk breaking working custom code

**DO:**
1. **Check if the changes are already applied** — The user's fork may already contain upstream changes via earlier manual patches or parallel development. Use `grep` to verify:
   ```bash
   grep -n "feature_name" target_file.py
   ```
2. **For changes that are NOT already applied**, extract the exact diff and apply surgically:
   ```bash
   git show upstream_commit_hash -- file.py > /tmp/patch.diff
   # Then manually apply only the relevant hunk
   ```
3. **For model additions** (like grok-4.3, deepseek-v4-pro), verify they're already in `hermes_cli/models.py` before attempting to add them again.
4. **Skip low-value changes when risk > benefit** — When upstream changes touch files with heavy custom modifications (training pipeline, cortex integration, gateway code), and the changes are nice-to-haves rather than critical fixes, **defer them**. Document what was skipped and why. The user's working pipeline is more valuable than marginal upstream features.

**Pattern: Verify-Before-Apply**
```bash
# Before any cherry-pick or patch:
for pattern in "grok-4.3" "deepseek-v4-pro" "trinity-large-thinking"; do
    grep -q "$pattern" hermes_cli/models.py && echo "✓ $pattern already present"
done
```

**Pattern: Defer-Risky-Changes**
```bash
# When upstream changes touch customized files:
# 1. Check if change is already applied (grep)
# 2. If not applied, assess: does this fix a bug I'm hitting, or add a feature I need?
# 3. If nice-to-have: echo "DEFERRED: <feature> — touches <custom_file>, risk > benefit"
# 4. If critical fix: apply surgically with manual patch, test immediately
```

This prevents redundant work, avoids corrupting files that already have the desired changes, and respects the user's preference for stability over feature completeness.

**User preference (May 6, 2026):** When asked about applying upstream changes that conflict with custom training pipeline code, user said "defer them" — working code > marginal features.

## Integration Branch Strategy (Divergent Git Histories)

When 400+ commits behind upstream with 100+ local commits, neither merge nor rebase is sane. Create an integration branch from upstream, selectively port custom files.

### When to Use
- Local branch has 100+ custom commits (905 in May 7 session)
- Upstream has 400+ new commits (441 in May 7 session)
- Direct merge would produce massive conflicts
- Running processes must not be interrupted (training PID 180722)

### Procedure
```bash
cd ~/hermes-agent

# 1. Fetch upstream
git remote add upstream https://github.com/NousResearch/hermes-agent.git 2>/dev/null
git fetch upstream main

# 2. Create integration branch from upstream
git checkout -b v0.13-integration upstream/main

# 3. Cherry-pick custom files by path (NOT by commit — history diverged)
git checkout qwen27b-training-artifacts-may3-2026 -- hermes_cli/subconscious/
git checkout qwen27b-training-artifacts-may3-2026 -- plugins/learning-brain/
git checkout qwen27b-training-artifacts-may3-2026 -- hermes_cli/instant_context.py
git checkout qwen27b-training-artifacts-may3-2026 -- custom_dflash/
# ... etc for each custom module

# 4. Fix import compatibility — add graceful fallbacks
# v0.13 removed StreamingThinkScrubber, added adaptive_injection
# Custom code importing removed modules will fail without guards:
#   try:
#       from hermes_brain import HermesBrain
#   except ImportError:
#       HermesBrain = None

# 5. Test imports before committing
python3 -c "from hermes_cli.subconscious.autobrowse_tracer import AutobrowseTracer"
python3 -c "import sys; sys.path.insert(0,'plugins/learning-brain'); import __init__"

# 6. Commit and push
git add .
git commit -m "v0.13 integration: port custom modules"
git push origin v0.13-integration
```

### Key Advantages
- **Zero risk to running processes**: Original branch untouched
- **Clean upstream base**: No merge conflicts, no rebase hell
- **Selective porting**: Only bring files that matter, skip garbage/backups
- **Testable**: Verify on integration branch before merging to main
- **Reversible**: If broken, `git checkout original-branch`

### Pitfalls
- **Import breakage**: Upstream v0.13 removed modules custom code depends on. Always add `try/except ImportError` guards with `None` fallback, then check `if Module is not None:` before use.
- **Hook signature changes**: v0.13 changed error handling in hooks (silent `pass` instead of `logger.debug`). Custom hooks still work but errors become invisible.
- **Plugin API drift**: v0.13 uses PluginContext object registration. Old dict-style `ctx["hook"] = callback` fails. Use `isinstance(ctx, dict)` backward-compat pattern.
- **UnicodeDecodeError in git show**: When checking if binary files exist via `git show`, use `git checkout` instead of parsing file content. `git show` on binary files produces decode errors in Python subprocess.

### Import Guard Pattern (Mandatory for v0.13+ Integration)
```python
# In plugins/learning-brain/__init__.py (or any custom plugin):
try:
    from hermes_brain import HermesBrain
except ImportError:
    HermesBrain = None

try:
    from context_updater import ContextUpdater
except ImportError:
    ContextUpdater = None

# In singleton getters:
def _get_brain():
    global _brain
    if _brain is None and HermesBrain is not None:
        _brain = HermesBrain()
    return _brain
```

This prevents startup failures when optional dependencies aren't installed or upstream modules moved.

## macOS sed Pitfall

`sed -i ''` on macOS uses different syntax than GNU sed. The `-i ''` (empty backup suffix) works, but complex patterns with `{}` and `d` commands fail with "extra characters at the end of d command".

**DON'T:**
```bash
# Fails on macOS:
sed -i '' '/pattern1/,/pattern2/{/pattern1/d;/pattern2/d}' file.py
```

**DO:** Use Python for complex conflict marker removal:
```python
import re

with open('file.py', 'r') as f:
    content = f.read()

# Remove git conflict markers, keeping v0.13 version (after =======)
def resolve_conflict(match):
    full = match.group(0)
    parts = full.split('=======')
    if len(parts) == 2:
        return parts[1].replace('>>>>>>> v0.13-integration', '').strip()
    return full

pattern = r'<<<<<<< HEAD.*?=======.*?>>>>>>> v0\.13-integration'
resolved = re.sub(pattern, resolve_conflict, content, flags=re.DOTALL)

with open('file.py', 'w') as f:
    f.write(resolved)
```

**Why:** Python regex handles multiline patterns reliably across platforms. sed's `{}` command grouping is implementation-specific and breaks on macOS BSD sed.

## Support Files

- `scripts/hermes_loop_guard.py` — Hard loop detection. Run before every tool call.
- `scripts/hermes_scheduler_daemon.py` — Cron scheduler with auto-cleanup for stuck flywheel cycles.
- `references/may3-2026-flywheel-cleanup-session.md` — Session log: 256h dead daemon, 51 stuck cycles, fix details.
- `references/dgx-training-death-may6-2026.md` — Qwen 27B training death at step 500: OOM during checkpoint save, empty checkpoint diagnosis, restart strategy.
- `references/dgx-training-oom-fix-may6-2026.md` — Four-phase CPU offload checkpoint save with try/except/finally and auto-resume logic.
- `references/tiered-memory-system-may6-2026.md` — Three-tier memory (hot/warm/cold) with auto-overflow, distillation, and promotion/demotion.
- `references/v0.13-integration-may7-2026.md` — Full session log: 441 upstream commits, 905 local commits, integration branch creation, selective porting, import guard fixes, merge conflict resolution.
- `references/persistence-layer-update-pattern.md` — Systematic protocol for updating all Hermes context files (MEMORY.md, SOUL.md, USER.md, MASTER.md) and verifying consistency across git repo, memory files, skills, and doctor output. Use when user says "update all persistence layers" or "sync everything".
- `references/persistence-layer-verification-checklist.md` — Post-update verification protocol. 8-step checklist to ensure all persistence layers are consistent after updates. Prevents drift where files disagree about system state.
- `scripts/autobrowse_injector.py` — Real-time autobrowse tip injector for CLI sessions. Records tool calls and generates pattern-based tips.
