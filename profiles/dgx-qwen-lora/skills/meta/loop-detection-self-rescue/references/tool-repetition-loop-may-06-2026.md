# Tool Repetition Loop — May 6, 2026

## Incident
During a training status check session, I fell into the same tool repetition pattern 3+ times despite the loop-detection skill being loaded:

1. **SSH grep loop**: `grep -n 'max_steps' train_lora_sae_teacher_v1.py` called 6 times consecutively with identical output — verifying the same config value repeatedly
2. **SSH test loop**: `python3 /tmp/test_checkpoint.py` called 4 times consecutively — same toy test, no new information
3. **Log verification loop**: `tail -5 /mnt/bigssd/train_lora_sae_teacher_v1_restart.log` called 3+ times — checking the same log position

## User Signals
- "loop?" — first callout
- "another loop?" — second callout, escalating frustration
- User expected me to self-detect after the first repetition

## Root Cause
The skill's detection rules focus on "same tool 3+ times" but miss:
- **Context drift**: When the PURPOSE of the tool call changes but the command stays similar (e.g., verifying different things with the same grep pattern)
- **Self-verification compulsion**: Re-checking facts already confirmed because of anxiety about being wrong
- **No progress metric**: No check for whether new information was actually obtained

## What Should Have Happened
After the first `grep` returned the config value, I should have:
1. Recorded the finding mentally
2. Moved to the NEXT question ("will it stop at 4000?")
3. Checked the stop condition code, not the config value again

## New Rule Added to Skill
**"Same command, different excuse" detection**: If you find yourself running the same command with a slightly different justification ("let me verify again", "just to be sure", "double-checking"), that's a loop. STOP after the first verification. Record the result and move forward.

## Prevention
- **Verification cap**: One check per fact. If you need to check again, you didn't trust the first result — fix the trust issue, not the fact.
- **Progress journal**: Before each tool call, state what new information you expect. If you can't articulate it, don't make the call.
