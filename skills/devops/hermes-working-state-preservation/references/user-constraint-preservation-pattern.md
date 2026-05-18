# User Constraint Preservation Pattern

## Date: 2026-05-16

## Problem

During a learning apparatus repair session, the user explicitly directed: **"do not touch the kimi model configuration"**. A prior incident had caused hours of recovery after the model config was accidentally changed. The repair needed to fix 8 issues while completely avoiding any modification to the kimi provider, model names, API keys, base URLs, or fallback configuration.

## The Constraint Preservation Protocol

When user says "don't touch X" or "stop doing X":

### 1. Immediate Acknowledgment
- Acknowledge the constraint explicitly in your response
- Document it in session notes
- Treat it as absolute — not a suggestion

### 2. Verify Every Action
Before executing ANY command or edit, mentally check: "Does this affect X?"
- File paths: Is X in the path?
- Config files: Does this file contain X settings?
- Shell commands: Do they reference X env vars or processes?
- Python scripts: Do they import or modify X modules?

### 3. Work Around, Not Through
If the fix requires touching X:
- Find an alternative approach that avoids X
- If no alternative exists, ASK the user before proceeding
- Document the dependency on X for future reference

### 4. Report Preservation in Summary
In the final summary, explicitly state: "X was preserved unchanged. No modifications to [specific fields]."

## Example Application

**User constraint:** "do not touch the kimi model config"

**Actions taken while preserving constraint:**
- Created memory files (`MEMORY.md`, `memory/` dir) — no config touched
- Fixed cron jobs by editing `~/.hermes/cron/jobs.json` — no config touched
- Created missing skills in `~/.hermes/skills/` — no config touched
- Verified hook wiring by reading `run_agent.py` and `model_tools.py` — no config touched
- Replaced corrupted `state.db` — no config touched
- Archived empty databases — no config touched
- Removed external `~/subconscious/` — no config touched

**What was NOT done:**
- No edits to `~/.hermes/config.yaml`
- No changes to `~/.hermes/.env`
- No modifications to provider settings
- No model name changes
- No base URL changes
- No API key changes

## Frustration Signals That Trigger This Protocol

| Signal | Meaning | Action |
|--------|---------|--------|
| "stop doing X" | Immediate halt on X | Stop X completely, preserve current state |
| "don't touch X" | Absolute constraint | Never modify X, work around it |
| "this is wrong" | Current approach broken | Stop, capture what works, pivot |
| "I spent hours getting this back" | Working state is precious | Preserve before any change |
| "holy shit you're back" | Recovery from loss | Capture immediately |
| "remember this" | Permanent preference | Embed in skill, not just memory |

## Integration with Working State Preservation

This pattern is a sub-protocol of the working state preservation system. When user expresses frustration about a specific component ("don't touch X"), that component becomes part of the "must preserve" set alongside auth, config, and source code.

**In the capture script:**
```bash
# Add to working-state-checklist.md
## User Constraints (Session-Specific)
- [ ] kimi model config — DO NOT MODIFY (2026-05-16)
- [ ] provider settings — frozen
- [ ] API keys — read-only
```

## Why This Belongs in a Skill, Not Just Memory

Memory captures "who the user is" (preferences, habits). Skills capture "how to do this class of task" (workflows, protocols). When a user says "don't touch X", it's both:
- A **memory** signal: "This user is protective of X"
- A **skill** signal: "When repairing systems, always check for user-protected components first"

The skill should carry the protocol; memory should carry the specific X values.
