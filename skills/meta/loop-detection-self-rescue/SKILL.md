---
title: Loop Detection & Self-Rescue
description: Detect and break out of repetitive tool-call loops before they waste tokens. Auto-escalates to the user with a concise alert.
name: loop-detection-self-rescue
trigger: When making the same type of tool call 3+ times in a row without meaningful progress, or when the user says "stuck in a loop", "stop looping", "break", etc.
---

# Loop Detection & Self-Rescue

## Problem
Agents fall into repetitive tool-call loops — same command, same result, no forward progress. This burns tokens and frustrates users.

## Detection Rules (MANDATORY — check before EVERY tool call)

**HARD STOP CONDITIONS — if any are true, STOP and escalate to user immediately:**

1. **Same-tool repetition**: If the last 3 tool calls were the same tool (e.g., terminal, web_search) with no user message in between → STOP
2. **Same-result repetition**: If the last 2 results were identical or contained the same error → STOP
3. **User trigger words**: User says "loop", "stuck", "stop", "break", "again?", "redundant", "you're in a loop", "stop looping" → IMMEDIATE STOP. Do not make another tool call.
4. **No-state-change**: After a tool call, check if any file was modified, any new data was fetched, or any decision was made. If none → STOP
5. **Verification loop**: If you've confirmed the same fact 2+ times and haven't applied the fix yet → STOP. Max 2 verifications, then act or escalate.
6. **Patch repetition**: If you apply a patch and it succeeds, DO NOT apply it again. Verify once, then move on.
7. **Command timeout**: If a command times out twice with the same inputs, STOP and escalate. Do not retry a third time with identical parameters.

## Hard Enforcement Mechanism

**The skill rules above are NOT sufficient.** Reading them does not prevent loops. You MUST implement a hard enforcement mechanism:

### Option A: External Loop Guard Script v2 (MANDATORY — INTENT-BASED)
**You MUST run this before EVERY tool call. Not optional. Not "when you remember". EVERY call.**

The loop guard tracks state externally and returns exit code 1 if a loop is detected. It is the ONLY reliable enforcement because skills are read once at session start then forgotten under pressure.

**CRITICAL: Use v2, not v1.** v1 only matched exact tool names. v2 matches **intent** — it catches loops where you call the same tool with slightly different arguments (e.g., 6 SSH calls with different grep patterns all hunting for the same info).

**Template:** `templates/hermes_loop_guard_v2.py` — deployed at `/tmp/hermes_loop_guard_v2.py`:

```bash
# BEFORE EVERY TOOL CALL — run this FIRST:
python3 /tmp/hermes_loop_guard_v2.py <tool_name> "<intent_description>" 2>/dev/null || { echo "LOOP GUARD BLOCKED"; exit 1; }

# Example before terminal command:
python3 /tmp/hermes_loop_guard_v2.py terminal "ssh-check-training-status" 2>/dev/null || { echo "LOOP BLOCKED"; exit 1; }
# Only if exit 0, proceed with the actual tool call

# Example before execute_code:
python3 /tmp/hermes_loop_guard_v2.py execute_code "run-python-analysis" 2>/dev/null || { echo "LOOP BLOCKED"; exit 1; }
```

**Intent naming convention:** Use short, descriptive strings:
- `ssh-check-training-status` — checking if training is alive
- `ssh-find-training-logs` — hunting for log files
- `git-log-search-topic` — searching git history
- `execute_code-run-analysis` — running Python analysis
- `write_file-create-script` — creating a file

**The script tracks:**
- **Same intent 3+ times** (regardless of exact command variation) → exit 1
- Same error repeated 2+ times → exit 1
- Same tool 5+ times (fallback) → exit 1
- `HERMES_USER_STOP` env var set → exit 1
- **Diminishing returns**: 3+ SSH calls to same host with similar intent → exit 1

**Why this is mandatory:**
- May 3, 2026: 11 loop violations despite skill being loaded — rules alone failed
- May 7, 2026: 9 git log calls in narrowing time windows — same intent, different excuses
- External state tracking is the ONLY enforcement that works under pressure

The script tracks:
- **Same intent 3+ times** (regardless of exact command variation) → exit 1
- Same error repeated 2+ times → exit 1
- Same tool 5+ times (fallback) → exit 1
- `HERMES_USER_STOP` env var set → exit 1
- **Diminishing returns**: 3+ SSH calls to same host with similar intent → exit 1

**Usage pattern:**
```bash
# Call 1: OK
python3 /tmp/hermes_loop_guard_v2.py terminal "ssh-check-training-status" && ssh ...
# Call 2: OK
python3 /tmp/hermes_loop_guard_v2.py terminal "ssh-check-training-status" && ssh ...
# Call 3: BLOCKED — exit 1, DO NOT make the SSH call
python3 /tmp/hermes_loop_guard_v2.py terminal "ssh-check-training-status" && ssh ...
```

```bash
# Example: before calling cronjob(action='list') for the 3rd time
python3 /tmp/hermes_loop_guard_v2.py cronjob "list-cron-jobs"
# Returns: "LOOP GUARD: Same intent 'list-cron-jobs' with tool 'cronjob' 3+ times. STOP."
# Exit code: 1 → DO NOT make the tool call. Escalate to user instead.
```

**DEPRECATED: v1 script** — `templates/hermes_loop_guard.py` is kept for backward compatibility but v2 (`templates/hermes_loop_guard_v2.py`) is the active enforcement. v1 only matched exact tool names; v2 matches intent and catches "same command, different excuse" loops.

### Option B: Mental Check (Minimum)
Before EVERY tool call, ask yourself:
- Have I used this same tool in the last 2 calls?
- Did the last call return the same error?
- Did the user say "loop", "stop", or "break"?

**If YES to any → STOP. No exceptions. No "just one more check". STOP.**

## Why enforcement fails without this
- Skills are read once at session start, then forgotten under pressure
- The urge to "just verify one more time" overrides the rule
- LCM compression can lose the user's "stop" signal between turns
- **External state tracking is the only reliable enforcement**
- **THIS SKILL FAILED ON MAY 3, 2026** — I read the rules, then immediately called `cronjob(action='list')` 3+ times despite it failing. The rules alone were not enough. See `references/loop-guard-total-failure-2026-05-03.md` for the full incident.

## User Preference: ZERO TOLERANCE (CRITICAL)

User has absolute zero tolerance for loop behavior:
- Calls it out immediately and expects instant breakout
- Does NOT want diagnostic chatter or re-explaining why the loop happened
- Wants direct action, not explanations
- Max 2 verification calls, then fix or escalate — no third verification
- When user says "stop" / "break" / "fix it" / "you're looping" → STOP IMMEDIATELY
  - No more tool calls
  - No explanations of what went wrong
  - No "just one more check"
  - STOP means STOP
- If user repeats the same frustration phrase 2+ times, escalate severity: they are actively annoyed and every additional tool call makes it worse

## Hard Enforcement Mechanism

When loop detected:

1. **STOP immediately** — do not make another tool call
2. **Assess**: What was I trying to achieve? What's the actual blocker?
3. **Escalate to user** with a concise alert:
   - "Detected loop: [brief description of what's repeating]"
   - "Blocker: [the actual error or missing piece]"
   - "Options: (A) [quick fix path] (B) [alternative path] (C) need your input on [specific question]"
4. **Wait for user direction** — do NOT auto-retry

## MAY 3 2026 SESSION: CATASTROPHIC SKILL FAILURE — LESSONS

**What happened**: Despite this skill being loaded and read at session start, I immediately fell into multiple loops:
1. Called `cronjob(action='list')` 3+ times despite it returning `{'error': "'id'"}` every time
2. Made 11 total loop guard violations in a single session
3. User had to physically say "STOP" multiple times with escalating force
4. The skill rules were NOT sufficient — reading them did not prevent loops

**Why it failed**:
- Skills are read once at session start, then forgotten under pressure
- The urge to "just verify one more time" overrides the rule
- LCM compression can lose the user's "stop" signal between turns
- **External state tracking is the only reliable enforcement**

**What actually worked**:
- `/tmp/hermes_loop_guard.py` — external script tracking tool calls via filesystem
- User saying "STOP" with force — but only after 11 violations
- Switching to alternative approaches (direct file access instead of broken tool)

**Updated hard rules** (enforced by loop guard script v2):
- Same intent 3+ times consecutively → STOP (exit code 1)
- Same error 2+ times → STOP (exit code 1)
- User says "loop"/"stop"/"break" → STOP immediately (exit code 1)
- Broken tool (first failure) → switch strategy, NO retries

**Verification**: Run `python3 /tmp/hermes_loop_guard_v2.py <tool_name> <intent_desc> [error_msg]` before EVERY tool call. If exit code 1, DO NOT make the tool call.

## Prevention Patterns

- **Before retrying a failed command**, change something meaningful: different args, different approach, or ask user
- **After 1 failure**, switch strategy — don't repeat with same inputs
- **Use `getattr` with defaults** for config objects instead of direct attribute access (see `references/qwen-config-sae-integration-fixes.md`)
- **Cache config lookups** — don't re-query the same data in a loop
- **Set hard limits**: max 2 retries per command, max 3 SSH calls per turn
- **Verification cap**: After 2 confirmations of the same fact, STOP and apply the fix or escalate. No third verification. (see `references/incident-qwen-config-loop-2026-05-01.md`)
- **Status monitoring**: Use cron for periodic checks, not manual conversation-loop polling. Stay silent after initial confirmation. (see `references/monitoring-sparse-status-pattern.md`)
- **SSH background execution**: NEVER use `&` in SSH commands — triggers foreground detection and kills the session. Use `terminal(background=true)` instead. (see `references/ssh-background-training-jobs.md`)
- **Resume command freshness**: When generating resume commands, ALWAYS query current state first. Stale resume commands (referencing old blockers, old PIDs, old file paths) waste user time and break trust. Query git status, process list, and file timestamps before composing. (see `references/resume-command-stale-state-incident.md`)
- **Process-polling loop guard**: When monitoring a background process, NEVER poll more than 3 times consecutively without meaningful state change. If the process output preview is identical across polls, or if the process has been running >5 minutes with no new log entries, STOP polling and either (a) check the log file directly, (b) run a health check command, or (c) escalate to user. DO NOT poll 10+ times hoping for change — that's a loop.
  - **For model loading / compilation waits**: Use `process.wait(timeout=300)` ONCE instead of rapid-fire polling. Model loading (e.g., Qwen 27B) takes ~3-4 minutes — polling every few seconds burns 40+ calls with zero value. Wait, then check logs. (see `references/process-polling-loop-incident-2026-05-03.md`)
  - **Hard cap**: 3 polls max per monitoring session. After 3, change strategy or escalate.
- **Tool-call loop on broken tools**: When a tool returns the SAME error repeatedly (e.g., `cronjob` tool returning `{'error': "'id'", 'success': False}`), STOP after the FIRST failure. Do not retry the same broken tool 2+ times. Switch to a workaround immediately (e.g., direct file editing, alternative tool, or escalate). (see `references/cronjob-tool-loop-pattern-2026-05-03.md`)
- **Terminal polling loop on SSH commands**: When checking remote process status via SSH, NEVER make the same `sshpass ssh ...` command more than 2 times consecutively without new information. If the output is identical across polls, STOP immediately. Use `process_poll` instead of SSH for background processes, or check log files directly. Polling the same SSH command 5+ times with identical output is a loop. (see `references/terminal-polling-loop-ssh-2026-05-05.md`)
- **SSH intent loop (May 7, 2026)**: When making SSH calls to check remote status, 3+ calls with the same underlying intent ("find training logs", "check GPU status") regardless of exact command variation is a loop. STOP at 3. The user expects synthesis from available data, not exhaustive hunting. (see `references/ssh-intent-loop-may-07-2026.md`)
- **SSH intent loop with loop guard v2 (May 7, 2026)**: v1 only matched exact tool names. v2 matches **intent** — it catches loops where you call the same tool with slightly different arguments (e.g., 6 SSH calls with different grep patterns all hunting for the same info). v2 deployed at `/tmp/hermes_loop_guard_v2.py`. Tests confirmed: 3 same-intent calls → exit 1. (see `references/ssh-intent-loop-may-07-2026.md`)
- **Tool-call repetition loop (general)**: When ANY tool (terminal, execute_code, skill_view, etc.) returns the same result or error across consecutive calls with identical or near-identical inputs, STOP after the second repetition. The user will call this out with phrases like "loop?", "another loop?", "stop looping". Do NOT wait for the third call — break on the second. Change strategy immediately: switch tools, change parameters, or escalate. (see `references/tool-repetition-loop-may-06-2026.md`)
- **"Same command, different excuse" loop**: If you find yourself running the same command with a slightly different justification ("let me verify again", "just to be sure", "double-checking"), that's a loop. STOP after the first verification. Record the result and move forward. The user expects self-detection, not repeated callouts. (see `references/tool-repetition-loop-may-06-2026.md`)
- **"Numbers change but it's still a loop"**: When searching through a large file with `sed`/`grep` line-by-line, the line numbers shift with each query. This makes it LOOK like progress ("the numbers change") but it's actually the same loop — you're still just dumping lines without achieving the goal. STOP after 3 consecutive `sed`/`grep` calls on the same file. Switch to `execute_code` with Python string manipulation for programmatic insertion/deletion. (see `references/tool-repetition-loop-may-06-2026.md`)
- **"Line-by-line log hunting loop"**: When user asks a direct question ("would X work?", "what is the answer?") and you respond by making 3+ SSH greps/seds/awks on the same log file, you are in a loop. The user wants a conclusion, not a line-by-line investigation. STOP after 2 log checks, synthesize what you know, and give the direct answer. If the user wants more evidence, they will ask. (see `references/direct-answer-delay-frustration-may8-2026.md`)
- **"Direct answer delay"**: When the user asks a question that can be answered from existing conversation context (e.g., "would rank 512 work with the fix?"), answer IMMEDIATELY without tool calls. Do NOT hunt for "one more piece of evidence" in logs. The user had to say "you said that 10 minutes ago — what is the answer?" and "loop?" to break me out of investigative mode. If the answer is knowable from context already established, give it in the first response. (see `references/direct-answer-delay-frustration-may8-2026.md`)
- **Hardwired config loop guard**: When user says "hardwire into hermes config yaml" or "hardwire it into config", they want loop guard settings permanently embedded in `~/.hermes/config.yaml` at multiple levels (agent, tool_loop_guardrails, delegation, code_execution). Do NOT just suggest settings — actually patch the config file. See `references/hermes-config-loop-guard-hardwire-2026-05-05.md` for exact settings.
- **Git commit timeout loop**: When git operations on remote machines hang (especially `git add .` with many untracked files), do NOT make more SSH calls to "fix" it. Each new SSH connection will also hang. STOP after the first timeout, escalate to user. (see `references/git-commit-timeout-loop-incident-2026-05-03.md`)
- **Compression loop guard**: When user says "stop", "pause", "save checkpoint", "going to bed" — these are TERMINAL commands. Do NOT continue with "just one more thing." Halt immediately, save state, confirm, and stop. Making tool calls after user says stop triggers LCM compression, which loses the stop signal, creating a loop. (see `references/compression-loop-incident-2026-05-03.md`)
- **Session-end loop guard**: When a cron task is fully completed and autonomous_decide returns idle with no new work from any source, accept [SILENT] as the final state without continued tool cycling. (see `references/session-end-silent-loop-2026-05-03.md`)
- **Auto-distillation saturation**: When auto-distillation produces 0 new tips, immediately switch to manual tip creation from fresh research findings — don't accept saturation as final. (see `references/auto-distillation-saturation-fix-2026-05-03.md`)
  - **Idle-state termination**: When confirming idle state 3+ times via autonomous_decide with no new work sources, accept termination gracefully instead of continuing to make tool calls. Avoid token waste from endless heartbeat loops. (see `references/idle-heartbeat-loop-2026-05-03.md`)

## Scheduler Daemon Pattern (for cron infrastructure)

When the Hermes cron scheduler is broken:
1. **STOP using the broken tool immediately** — do not retry `cronjob()` after it fails
2. Check `~/.hermes/cron/jobs.json` directly with Python/json instead
3. Fix scheduler bugs in `cron/jobs.py` (e.g., `rj.get("id")` instead of `rj["id"]`)
4. Start a simple daemon wrapper: `python3 /tmp/hermes_scheduler_daemon.py`
5. The daemon runs `tick()` every 60s and executes due jobs
6. Monitor output in `~/.hermes/cron/output/<job_id>/`

**Critical:** The `cronjob` tool returning `{'error': 'id'}` is a broken tool. Do NOT call it again. Use direct file access instead. See `references/cron-scheduler-daemon-pattern-2026-05-03.md` for full details including the daemon code, API key export, and mass-disable/re-enable workflow.

**Auto-cleanup for stuck cycles:** Any daemon that inserts "running" rows into a database must also kill rows older than 2× expected completion time. See `references/scheduler-daemon-cleanup-pattern-2026-05-03.md` for the pattern and real-world example (51 stuck cycles → 3 after cleanup).
**Critical:** The `cronjob` tool returning `{'error': 'id'}` is a broken tool. Do NOT call it again. Use direct file access instead. See `references/cron-scheduler-daemon-pattern-2026-05-03.md` for full details including the daemon code, API key export, and mass-disable/re-enable workflow.
- **Compression loop guard**: When user says "stop", "pause", "save checkpoint", "going to bed" — these are TERMINAL commands. Do NOT continue with "just one more thing." Halt immediately, save state, confirm, and stop. Making tool calls after user says stop triggers LCM compression, which loses the stop signal, creating a loop. (see `references/compression-loop-incident-2026-05-03.md`)
- **Git commit timeout loop**: When git operations on remote machines hang (especially `git add .` with many untracked files), do NOT make more SSH calls to "fix" it. Each new SSH connection will also hang. STOP after the first timeout, escalate to user. (see `references/git-commit-timeout-loop-incident-2026-05-03.md`)

## Example Alert Format

```
⚠️ LOOP BREAK
Repeating: SSH config attribute checks
Blocker: Qwen3_5Config missing hidden_size (need to inspect actual config object)
Options:
  (A) Use getattr() with safe defaults
  (B) Print all config attributes to find the right one
  (C) Which model variant are you targeting?
```

## Memory Tag
Save loop incidents to memory with pattern: "LOOP: [tool] ×[count] on [task] → [resolution]"
