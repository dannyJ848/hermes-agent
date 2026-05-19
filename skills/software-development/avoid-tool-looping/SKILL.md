---
name: avoid-tool-looping
description: "Recognize and break out of repetitive tool-call loops during debugging or verification tasks."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [debugging, workflow, anti-pattern, looping, terminal]
---

# Avoid Tool Looping

A common failure mode during complex debugging or verification tasks is getting stuck in a loop of identical or nearly-identical tool calls — repeatedly checking the same status, running the same command with minor variations, or verifying the same thing multiple times without making progress.

## Recognizing the Loop

Signals you are looping:
- Same command run 3+ times with same result
- User says "loop?" or "stop looping"
- Output is identical to previous iteration
- No new information gained between calls
- Feeling "stuck" or unsure what to do next

## Breaking the Loop

### 1. Stop and Analyze

When you notice repetition:
1. **Do NOT run the same command again**
2. Ask: "What new information do I expect to gain?"
3. If answer is "none" — stop, think, change strategy

### 2. Change Information Source

Instead of repeating the same terminal command:
- Read source code to understand behavior
- Check configuration files for settings
- Look at logs instead of status commands
- Use `git diff` or `git show` to inspect changes
- Search for related code with `grep` or `find`

### 3. Escalate the Approach

If verification keeps failing:
- Try a completely different verification method
- Look for the root cause instead of symptoms
- Check if there's a caching issue (restart service, clear cache)
- Consider if the problem is environmental (wrong Python version, wrong directory)

### 4. Ask for Help

If truly stuck after 2-3 different approaches:
- Summarize what you've tried
- Explain what you expected vs what happened
- Ask user for guidance or confirmation

## Common Loop Scenarios

### Git Status Loop
```bash
# BAD: Repeating git status hoping for different result
git status
git status
git status

# GOOD: Check what's actually happening
git diff --stat HEAD
git log --oneline -5
git ls-files -o -m
```

### Skill Count Loop
```bash
# BAD: Repeatedly counting skills
count skills
count skills
count skills

# GOOD: Check configuration loading
hermes config get skills.external_dirs
grep -r "external_dirs" config.yaml
cat skills/.bundled_manifest
```

### Process Check Loop
```bash
# BAD: Repeatedly checking if process is running
ps aux | grep myprocess
ps aux | grep myprocess

# GOOD: Check logs, check systemd, check port
journalctl -u myservice -n 20
systemctl status myservice
ss -tlnp | grep :8080
```

## Prevention

Before running a command:
1. State what you expect to learn
2. If result is X, I will do Y
3. If result is not X, I will try Z (different approach)
4. Never "check again just to be sure"

## User Intervention

When user says:
- "loop?" → Immediately stop, acknowledge, change strategy
- "stop doing X" → Stop X, ask what to do instead
- "this is too verbose" → Reduce output, be concise
- "just give me the answer" → Skip explanations, provide result

## Rule of Three

Never run the same command more than 3 times in a session. If you need a 4th verification, you are looping. Stop and rethink.
