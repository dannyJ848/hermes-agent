# Minimal-Response Debugging Mode

## Date: 2026-05-18

## The Signal

When the user emits frustration signals during debugging:
- "sorry sorry sorry sorry"
- "just fix it"
- "stop talking"
- "why are you explaining"
- "just give me the answer"
- "you always do Y and I hate it"
- "don't format like this"
- "this is too verbose"

**Meaning:** The user wants rapid minimal-response interaction. They are in debugging mode and want fixes, not conversation.

## The Protocol

### 1. Stop Talking

- No explanations of what went wrong
- No "here's what I found" narratives
- No reasoning about root cause unless asked
- No apologies or acknowledgment of mistakes

### 2. Report the Fix

State what you did in one line:
- "Fixed: added _vprint method after __init__"
- "Fixed: added log_prefix after self.verbose"
- "Fixed: added max_total_size_mb and max_file_size_mb to CheckpointManager"

### 3. Confirm It Works

Run the verification. Report result in one line:
- "hermes starts clean now"
- "CLI loads without errors"
- "Push succeeded"

### 4. Move On

If there's more work, ask a single concise question:
- "Next: verify vLLM on DGX?"
- "Next: test tool calling?"

If there's nothing more, stop. Don't summarize. Don't ask if there's anything else.

## What NOT To Do

| Don't | Why |
|-------|-----|
| "I apologize for the confusion" | User doesn't want apologies, they want fixes |
| "Here's what happened..." | User doesn't want narrative |
| "The root cause was..." | User doesn't want root cause analysis |
| "Let me explain the fix..." | User doesn't want explanation |
| Multiple messages for one fix | Each message is friction |
| "Does that work for you?" | User will tell you if it doesn't |

## When To Switch Back To Normal Mode

The user will switch back by:
- Asking a question that requires explanation
- Saying "explain that" or "why did that happen"
- Moving from debugging to planning/discussion
- Explicitly saying "ok, let's talk about next steps"

Until then, stay in minimal-response mode.

## Why This Is a Skill, Not Just Memory

This is a **task-class preference** (how to behave during debugging), not a user trait (who the user is). The preference is specific to the debugging context — the same user may want thorough explanations during planning or research. The skill carries the context-specific protocol; memory carries the general user profile.
