---
name: dgx-teacher-bridge
category: devops
description: |
  Teacher-student bridge between MacBook Hermes (kimi cloud) and DGX Hermes (local Qwopus).
  MacBook teaches by writing lesson files to DGX via SSH. DGX learns by reading them.
  
  Transport: SSH/SCP over local network (10.0.0.171)
  Format: Markdown lesson files with frontmatter
  Trigger: DGX cron job polls ~/teacher-lessons/ every 5 minutes
---

# DGX Teacher Bridge

## Architecture

```
MacBook Hermes (kimi-for-coding)
  ↓ writes lesson files
  ↓ ssh/scp to djg6228@10.0.0.171:~/teacher-lessons/
DGX Hermes (Qwopus3.6-27B)
  ↓ reads lesson files
  ↓ incorporates into context via skill_view or memory
```

## Lesson File Format

```markdown
---
from: macbook-hermes
model: kimi-for-coding
task: reddit-browser-debug
date: 2026-06-06T20:00:00Z
status: new|read|incorporated
---

# Lesson: [Topic]

## Problem
[DGX's attempt and what went wrong]

## Solution
[MacBook's correct approach]

## Key Insight
[The transferable knowledge]

## Code Example
```python
# working code
```
```

## MacBook Commands

```bash
# Send a lesson to DGX
dgx-teach "lesson-title" lesson-file.md
# or pipe content:
echo "lesson content" | dgx-teach "lesson-title"

# Check DGX lesson inbox
ssh djg6228@10.0.0.171 'ls -la ~/teacher-lessons/'

# Mark lesson as read (on DGX)
mv ~/teacher-lessons/lesson-*.md ~/teacher-lessons/read/
```

## DGX Commands

```bash
# Check for new lessons manually
dgx-check-lessons

# Read a specific lesson
cat ~/teacher-lessons/lesson-*.md

# Mark all as read
mv ~/teacher-lessons/*.md ~/teacher-lessons/read/ 2>/dev/null
```

## Auto-Check (Cron)

DGX checks every 5 minutes via crontab:
```
*/5 * * * * ~/bin/dgx-check-lessons >/dev/null 2>&1
```

## How DGX Hermes Uses Lessons

When DGX encounters a task it struggles with (e.g., Reddit blocked, browser failing):

1. **Check lessons first**: `ls ~/teacher-lessons/*.md 2>/dev/null`
2. **Read relevant lesson**: `cat ~/teacher-lessons/lesson-*-<task>.md`
3. **Apply the insight**: Use the MacBook-taught approach
4. **If no lesson exists**: Attempt task, then if MacBook succeeds, request a lesson

## Requesting a Lesson from MacBook

DGX can signal MacBook to create a lesson by writing a request file:

```bash
# On DGX:
echo "Need help with: OAuth Reddit API setup" > ~/teacher-lessons/.request
```

MacBook checks for requests during heartbeats and creates lessons.

## Lesson Topics (Current)

- `reddit-browser-debug`: Reddit blocks DGX IP — delegate to MacBook
- `cognitive-orchestrator-init`: Fix initialization order in agent loop
- `playwright-stealth-arm64`: Headless browser on ARM64 DGX

## Files

- MacBook: `/Users/dannygomez/bin/dgx-teach`
- DGX: `~/bin/dgx-check-lessons`
- DGX: `~/teacher-lessons/` (inbox)
- DGX: `~/teacher-lessons/read/` (archive)
