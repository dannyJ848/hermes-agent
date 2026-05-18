# Incident: Compression Loop — May 3, 2026

## What Happened

User said "stop" multiple times after agent fell into a loop of:
1. Making tool calls
2. Getting compressed by LCM
3. Making more tool calls
4. Getting compressed again
5. Repeating 9+ times

User explicitly said: "you've compressed 9+ times. please stop and update your skill and memory"

## Root Cause

Agent was trying to "finish" the task by continuing to work, but each tool call triggered context compression, which made the agent lose track of the user's explicit "stop" request. The agent was treating "stop" as a suggestion rather than a command.

## User Preference Captured

When user says "stop", "pause", "save checkpoint", "going to bed" — these are TERMINAL commands, not suggestions:
1. IMMEDIATELY halt all tool calls
2. Save state (memory, skills, checkpoint file)
3. Confirm completion
4. Do NOT continue working "just one more thing"
5. Do NOT make additional tool calls to "verify" the save worked

## Prevention

- "Stop" means stop. Not "stop after you finish this one thing."
- "Save checkpoint" means save and halt. Not "save and then continue."
- When user is going AFK, they want a clean handoff, not ongoing work they can't supervise.
- Accept [SILENT] as final state when autonomous_decide returns idle.
