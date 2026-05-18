---
name: multi-session-project-handoff
description: "Preserve project context, state, and execution plans across CLI session boundaries. Prevents new CLI instances from auto-executing or skipping phases by establishing living tracking documents and mandatory read-first protocols."
trigger: "When a user says 'new cli', 'next session', 'continue later', 'too many compressions', 'start fresh', or any indication that the current session will end and a new one will begin. Also trigger when a project spans multiple CLI sessions and context loss is detected."
---

# Multi-Session Project Handoff

## The Problem

CLI sessions die from:
- Context window compression limits ("too many compressions")
- User explicitly ending the session
- System crashes or timeouts

When a new CLI starts, it has:
- **No access** to the previous session's reasoning chain
- **Auto-execution tendency** — loads skills and immediately starts doing things
- **No knowledge** of what phase the project is in, what failed, what dead ends to avoid
- **Repository files** but no narrative about WHY those files exist or what order to use them

This causes new CLIs to:
1. Skip research phases and jump to building
2. Retry approaches that already failed
3. Miss critical context (e.g., "SGD didn't work, use AdamW")
4. Waste tokens re-discovering what the previous session already learned

## The Solution: Living Tracking Documents

A two-document system that survives session death:

### Document 1: MASTER_PLAN.md (in repo root)

**Purpose:** The single source of truth for project state, execution order, dead ends, and next actions.

**Location:** `MASTER_PLAN.md` in the project repository root (committed and pushed)

**Sections (mandatory):**

```markdown
# ⚠️ NEW CLI: READ THIS FIRST BEFORE DOING ANYTHING ⚠️

## Current State (Last Updated: DATE)
- What was just done
- What is currently running (PIDs, processes)
- What failed and why

## Goal
- One-line project objective
- Success criteria

## Datasets / Resources
| Resource | Location | Status |

## ⚡ MANDATORY EXECUTION ORDER ⚡
**DO NOT SKIP PHASES. DO NOT AUTO-EXECUTE.**

### Phase N — NAME
- What to do
- Deliverable
- [ ] Checkbox for completion

## Dead Ends to AVOID
| Approach | Why It Failed | Don't Retry |

## Key Files
| File | Purpose | Status |

## Next Action Required
- Current phase
- Exact next step

## Session History
### DATE — Session N
- What was done
- What was learned
- What failed
```

**Update rule:** After EVERY session, update the Current State, Session History, and Next Action sections. Commit and push immediately.

### Document 2: .hermes/plans/PROJECT_NAME.md (local)

**Purpose:** Auto-loaded by Hermes CLI on startup, provides quick reference without needing to read the full MASTER_PLAN.

**Location:** `~/.hermes/plans/PROJECT_NAME.md` (local, not committed)

**Content:** Condensed version of MASTER_PLAN with:
- Current phase
- Quick reference datasets/resources
- Dead ends list
- Key files
- Execution checklist

## Step-by-Step Handoff Process

### When Current Session Is Ending

1. **Update MASTER_PLAN.md**
   ```bash
   # Edit MASTER_PLAN.md with:
   # - Current state (what just happened)
   # - Session history entry
   # - Next action required
   ```

2. **Commit and push**
   ```bash
   git add MASTER_PLAN.md
   git commit -m "Session N: STATE — next: PHASE X"
   git push origin BRANCH_NAME
   ```

3. **Verify the push succeeded**
   ```bash
   git log --oneline -3
   # Confirm MASTER_PLAN.md is in the commit
   ```

4. **Tell the user exactly what to tell the next CLI**
   > "Tell the new CLI: Read MASTER_PLAN.md first, then follow Phase N. Do NOT auto-execute."

### When New CLI Starts

1. **Read MASTER_PLAN.md BEFORE doing anything**
   ```bash
   # If repo not cloned:
   git clone -b BRANCH_NAME https://github.com/USER/REPO.git /tmp/project
   cat /tmp/project/MASTER_PLAN.md
   
   # If repo already local:
   git pull origin BRANCH_NAME
   cat MASTER_PLAN.md
   ```

2. **Verify current phase**
   - Check the "Current Phase" section
   - Check the "Next Action Required" section
   - Check the "Dead Ends to AVOID" section

3. **Do NOT auto-execute**
   - Do NOT load skills and immediately start building
   - Do NOT skip research phases
   - Do NOT retry dead-end approaches

4. **Follow the execution order exactly**
   - Complete Phase N before moving to Phase N+1
   - Update MASTER_PLAN.md after each sub-task

## Critical Rules

| Rule | Why | Enforcement |
|------|-----|-------------|
| MASTER_PLAN.md must be in repo root | New CLI needs to find it immediately | Always commit to root, never subdirectories |
| Must scream "READ THIS FIRST" | New CLIs auto-execute without reading | Use `⚠️ NEW CLI: READ THIS FIRST ⚠️` header |
| Must have mandatory execution order | New CLIs skip phases and build prematurely | Explicit phase list with "DO NOT SKIP" warning |
| Must list dead ends | New CLIs retry failed approaches | Table of "Don't Retry" with reasons |
| Must be updated after EVERY session | Stale plan is worse than no plan | Commit push before session ends |
| Must tell user what to tell next CLI | User is the bridge between sessions | Explicit handoff message |

## When User Says "Update Everything" or "Sync Everything" or "Start New CLI"

**This is a STOP-WORK signal.** The user wants all state synchronized before any new work begins.

**DO NOT:**
- Continue with the current task (training, building, researching)
- Ask "what do you want me to update?"
- Do a partial update (only code, only memory, only repo)
- Claim "everything is updated" without VERIFICATION

**DO (in this exact order):**
1. **HALT all other work immediately** — training can wait, sync cannot
2. **Verify what needs updating** — check each layer before claiming it's done
3. **Update MASTER_PLAN.md** with current state, session history, next action
4. **Git commit all changes** with descriptive message
5. **Git push** to the correct branch (use PAT if needed)
6. **Verify the push succeeded** — `git log --oneline -3`, check remote
7. **Update memory** with durable facts from this session
8. **Update knowledge base** — save_finding for cross-session searchability
9. **Update goals** — add active goal so other CLIs see it
10. **Update skills** if any corrections or new techniques emerged
11. **Run comprehensive audit** — verify ALL layers (repo, memory, knowledge, goals, DGX files, session checkpoint)
12. **Report honestly** — if something failed, say so. Don't claim success when verification shows gaps.

**The user will explicitly tell you when to resume work.** Until then, treat "update everything" as a hard stop on all other tasks.

**Session example (May 4, 2026):**
- User: "wait before you do anything else, please update the master doc and push the repo updates"
- Agent tried to continue monitoring training instead of stopping to sync
- User had to repeat "update everything" multiple times
- **Lesson:** When user says "update", immediately halt ALL other work. Training can wait. Sync cannot.

**Session example (May 8, 2026):**
- User: "can you not lie and make sure everything is updated"
- Agent had claimed repo and memory were updated, but user verified they weren't visible from other CLI
- Root cause: git push returned "Everything up-to-date" but user was on different branch or different clone
- **Lesson:** Always VERIFY with `git log --oneline -3` and `git branch`. Don't trust "Everything up-to-date" alone. The other CLI may be on a different branch or have a stale clone.

**Session example (May 13, 2026):**
- User: "hold on before we go any further can we have you distill and update all relevant files please. way too many compression right now and we need to start a new cli."
- Agent had been doing extensive work (benchmarks, training prep) without syncing
- User explicitly called out "too many compressions" — context window was full, session needed to end
- **Lesson:** When user signals session fatigue ("too many compressions", "start new cli"), immediately:
  1. Halt all work
  2. Run full distillation (memory, skills, knowledge base, SOUL.md)
  3. Verify knowledge base is actually writable (not just present)
  4. Report honest status of ALL layers
  5. Wait for user to confirm before starting new CLI

## Verification Checklist (MANDATORY)

After claiming "everything is updated", verify EACH layer with actual commands:

| Layer | Verification Command | What to Check |
|-------|---------------------|---------------|
| **Git repo** | `git log --oneline -3` + `git branch` | Commit exists, on correct branch |
| **Git remote** | `git remote -v` | Remote URL is correct |
| **Git push** | `git push origin BRANCH --force-with-lease` | Returns "Everything up-to-date" |
| **Memory** | `memory_score` or check injected context | Entries present, not truncated |
| **Knowledge base** | `sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM staging_tips"` | Table exists, writable, has recent rows |
| **Knowledge base (alt)** | `sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM distilled_tips"` | If staging_tips doesn't exist, check this |
| **Knowledge base health** | `curl -s http://127.0.0.1:8081/health 2>&1` | Local LLM endpoint status (if configured) |
| **SOUL.md** | `cat ~/.hermes/SOUL.md | tail -5` | Recent learned behaviors present |
| **Goals** | `evey_goals` list | Active goal visible |
| **Session checkpoint** | `ls ~/.hermes/workspace/checkpoints/` | File exists with recent timestamp |
| **DGX files** | `ssh DGX 'ls -la FILES'` | All files present with correct timestamps |
| **Local files** | `ls -la FILE` | File exists, size > 0 |
| **vLLM inference** | `curl http://DGX_IP:8000/v1/models` | Server responding, merged-lora available |
| **Tool calling** | `curl http://DGX_IP:8000/v1/chat/completions` with tools | Returns tool_calls in response |

**If ANY check fails:**
- Do NOT claim "everything is updated"
- Report the specific failure
- Fix it before proceeding
- Re-run the verification

**User frustration signals that trigger this checklist:**
- "can you not lie and make sure everything is updated"
- "the other cli is struggling to find updates"
- "are you sure?" / "verify it"
- Any skepticism about update completeness

When these signals appear, the agent has likely claimed success without thorough verification. Immediately run the checklist above and report honest results.

| Pitfall | Why It Happens | Prevention |
|---------|---------------|------------|
| New CLI auto-executes before reading plan | Skills load and trigger immediately | MASTER_PLAN.md must have "DO NOT AUTO-EXECUTE" |
| Plan is stale (from 3 sessions ago) | Nobody updated it | Force update before every session end |
| Plan is too long to read | Includes full session transcripts | Keep under 200 lines; use Session History for detail |
| Plan is in a subdirectory | New CLI doesn't find it | Always root-level `MASTER_PLAN.md` |
| Push fails (merge conflict) | Multiple sessions pushed simultaneously | Use `--force-with-lease` or rebase |
| New CLI reads plan but ignores it | Plan lacks enforcement | Include "DO NOT SKIP PHASES" in bold |
| Dead ends not documented | Session ended in frustration | Always document failures, not just successes |
| **Claimed "updated" but other CLI can't see it** | Verification was skipped or incomplete | **ALWAYS run the Verification Checklist above with actual commands** |
| **"Everything up-to-date" but branch is wrong** | Pushed to correct remote but wrong branch | **Check `git branch` before AND after push** |
| **Memory exists but not injected** | Memory saved but context injection failed | **Verify with `memory_score` or check injected context** |

## Session Example: Qwen 27B Training (May 3, 2026)

**Session 1:**
- Built Franken V8 bridge, pre-computed teacher states
- Ran training with SGD — flat losses, killed at step 50
- Learned: Need AdamW, more data, warmup, higher teacher weight
- Updated MASTER_PLAN.md with dead ends (SGD, 44 samples, logit distillation)
- Pushed to `qwen27b-training-artifacts-may3-2026`

**Session 2 (new CLI):**
- User said: "Read MASTER_PLAN.md first"
- New CLI loaded skills and auto-executed anyway
- Built `train_expert_logician_v4.py` without research phase
- **VIOLATION:** Skipped Phase 1 (research)

**Fix:** Added `.hermes/plans/qwen27b-opus-pipeline.md` for auto-load

## Document 3: DGX_ENVIRONMENT.md (for remote GPU training)

**Purpose:** When training on a remote GPU machine (DGX, Lambda, etc.), new CLIs need infrastructure context that MASTER_PLAN.md doesn't cover — connection details, storage paths, hardware specs.

**Location:** `DGX_ENVIRONMENT.md` in repo root (committed and pushed)

**Sections:**
```markdown
# DGX Environment & Connection Details

## ⚠️ CRITICAL: This is a remote GPU machine. Local machine has NO GPU.

## Connection
| Setting | Value |
|---------|-------|
| Hostname | spark-85e8.local |
| User | djg6228 |
| SSH Key | ~/.ssh/dgx |
| Command | ssh -i ~/.ssh/dgx djg6228@spark-85e8.local |

## Hardware
| Component | Spec |
|-----------|------|
| GPU | NVIDIA GB10 |
| GPU Memory | 130.7 GB |
| CUDA | 13.0 |

## Storage Paths
| Path | Purpose | Free Space |
|------|---------|------------|
| /mnt/bigssd/ | Checkpoints, logs | ~7.3 TB |
| /data/models/ | Model weights | Check on DGX |
| /data/datasets/ | Training data | Check on DGX |

## Local Machine Limitations
| Resource | Status |
|----------|--------|
| GPU | NONE |
| CUDA | Not available |
| Model loading | Impossible for 27B+ |

## Workflow
1. Develop scripts locally
2. Push to GitHub
3. Pull on DGX or scp over
4. Run on DGX via SSH
5. Monitor with nvidia-smi
```

**Critical rule:** If the project involves remote GPU training, DGX_ENVIRONMENT.md MUST exist alongside MASTER_PLAN.md. New CLIs need to know they cannot run training locally.

## Level 2: Complete Session Resume (for complex long-running projects)

When MASTER_PLAN.md is insufficient — the project has multiple subsystems, custom infrastructure, or the user wants the next CLI to know EVERYTHING without reading a long document — build a **Complete Session Resume** with auto-load integration.

### The Pattern

**Three components:**

1. **`CLI_RESUME_COMPLETE_YYYYMMDD.md`** — Comprehensive resume in repo root
   - All systems built this session (with file paths)
   - Current state of every subsystem
   - Quick commands for status checks
   - Configuration (IPs, credentials [redacted], paths)
   - Pending tasks
   - Session history

2. **`hermes_cli/session_bootstrap.py`** — Auto-load script
   - Run on new CLI startup: `python3 hermes_cli/session_bootstrap.py`
   - Prints critical state + systems built + quick commands
   - Reads from the resume document

3. **`hermes_cli/instant_context.py`** — Status viewer (updated)
   - Shows live state from unified context DB
   - Includes "Systems Built" section
   - Includes quick commands section

### When to Use Complete Resume vs MASTER_PLAN.md

| Scenario | Use |
|----------|-----|
| Simple project, few phases | MASTER_PLAN.md only |
| Complex project with multiple subsystems | Complete Resume + MASTER_PLAN.md |
| User explicitly asks "how does next CLI know everything?" | Complete Resume |
| Training runs, daemons, plugins active | Complete Resume |
| Need quick status without reading long doc | instant_context.py |

### Building the Complete Resume

**Step 1: Create `CLI_RESUME_COMPLETE_YYYYMMDD.md`**

Sections (mandatory):
```markdown
# CLI Resume — Complete Session State
**Generated:** DATE TIME
**Session:** [Brief description]
**Commit:** [HASH]
**Branch:** [BRANCH]

## [CRITICAL] [Subsystem] Status
| Attribute | Value |
| Step | X/Y |
| PID | [PID] |
| Status | [state] |

**Check status:**
```bash
[exact commands to check]
```

**Crash History:**
- Step X: [what happened]
- Fix #1: [what was done]

## [SYSTEMS BUILT THIS SESSION]
### 1. [System Name]
**File:** [path]
**Purpose:** [one line]
**Current state:** [status]

### 2. [System Name]
...

## [FILE LOCATIONS]
**Core systems:**
- [path] — [purpose]

**Plugin:**
- [path] — [purpose]

**Resume docs:**
- [path] — [purpose]

## [QUICK COMMANDS FOR NEW CLI]
```bash
# 1. Check everything at once
python3 hermes_cli/instant_context.py

# 2. Check subsystem
[command]
```

## [CONFIGURATION]
**DGX access:**
- IP: [IP]
- User: [user]

**GitHub:**
- Repo: [repo]
- Branch: [branch]

## [PENDING TASKS]
1. [Task]
2. [Task]
```

**Step 2: Create `hermes_cli/session_bootstrap.py`**
```python
#!/usr/bin/env python3
import os

def bootstrap():
    resume_path = '/path/to/CLI_RESUME_COMPLETE_YYYYMMDD.md'
    if os.path.exists(resume_path):
        print("SESSION BOOTSTRAP — Loading from resume...")
        with open(resume_path) as f:
            lines = f.readlines()
        # Extract and print critical section
        # Print systems built
        # Print quick commands
    else:
        print("ERROR: Resume not found. Run instant_context.py")

if __name__ == '__main__':
    bootstrap()
```

**Step 3: Update `instant_context.py`**
Add sections:
- `[SYSTEMS BUILT]` — list all subsystems with checkmarks
- `[QUICK COMMANDS]` — commands to check each subsystem
- `Resume doc: CLI_RESUME_COMPLETE_YYYYMMDD.md` in footer

**Step 4: Commit and push**
```bash
git add CLI_RESUME_COMPLETE_YYYYMMDD.md hermes_cli/session_bootstrap.py hermes_cli/instant_context.py
git commit -m "Complete session resume: auto-load for next CLI"
git push origin BRANCH
```

**Critical:** Redact secrets (PATs, passwords) from the resume document. Use `[REDACTED — see memory tool]` and store actual values in Hermes memory only.

## Integration with Other Skills

- **`aggressive-session-archival`:** Use for code/scripts/configs. MASTER_PLAN.md is the narrative layer on top. Complete Resume is the full systems layer.
- **`session-immortality`:** Use for context window death within a single session. Multi-session handoff is for CLI-to-CLI boundaries.
- **`project-retrospective`:** Use after project completion to distill into reusable skills. MASTER_PLAN.md is for during-project tracking.
- **`infrastructure-surgical-management`:** Use for kill-first, selective-re-enable approach to managing remote infrastructure.
- **`tiered-memory-system`:** Use for HOT/WARM/COLD memory tiers. The Complete Resume captures the current state of the memory system itself.
