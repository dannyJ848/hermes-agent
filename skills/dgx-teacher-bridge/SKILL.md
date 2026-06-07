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

## When DGX Should Request a Lesson

**Use the `request_lesson` tool when:**
- Web scraping fails due to IP blocks (Reddit, etc.)
- Browser automation is blocked by bot detection
- A tool consistently fails after 3+ attempts
- You need knowledge MacBook has (API keys, proxies, etc.)
- You see patterns like "connection refused", "403 Forbidden", "blocked"

**Do NOT request a lesson for:**
- Syntax errors in your own code (fix those yourself)
- Logic bugs (debug those yourself)
- Tasks DGX can complete successfully

## How to Request a Lesson (DGX)

```
request_lesson(
    task="reddit-browser-debug",
    what_went_wrong="Reddit blocks DGX IP at network level. All approaches failed: curl, browser, old.reddit.com",
    attempted_approaches="curl with headers, browser tool, old.reddit.com, kimi webbridge"
)
```

This writes a request file to ~/teacher-lessons/. MacBook detects it and creates a lesson.

## How to Check for Lessons (DGX)

```
check_lessons()
```

Returns count and list of available lessons. If lessons exist, read them:

```
read_lesson(lesson_name="lesson-20260606-200359-reddit-browser-debug.md")
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

# Check for DGX requests
macbook-check-requests
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

1. **Try 2-3 times yourself first** — don't immediately give up
2. **If still failing**: Use `request_lesson` tool to ask MacBook
3. **Wait for lesson**: MacBook creates and sends it (usually within minutes)
4. **Check for lessons**: Use `check_lessons` to see if new lessons arrived
5. **Read and apply**: Use `read_lesson` to get the content, then apply the approach
6. **Mark as read**: Move lesson to read/ subdirectory

## Requesting a Lesson from MacBook

DGX can signal MacBook to create a lesson by using the `request_lesson` tool:

```
request_lesson(
    task="reddit-oauth-setup",
    what_went_wrong="Reddit blocks DGX IP. Need OAuth API approach from MacBook.",
    attempted_approaches="curl, browser, old.reddit.com"
)
```

MacBook checks for requests during heartbeats and creates lessons.

## Lesson Topics (Current)

- `reddit-browser-debug`: Reddit blocks DGX IP — delegate to MacBook
- `cognitive-orchestrator-init`: Fix initialization order in agent loop
- `playwright-stealth-arm64`: Headless browser on ARM64 DGX

## Files

- MacBook: `/Users/dannygomez/bin/dgx-teach`
- MacBook: `/Users/dannygomez/bin/macbook-check-requests`
- DGX: `~/bin/dgx-check-lessons`
- DGX: `~/bin/dgx-request-lesson`
- DGX: `~/teacher-lessons/` (inbox)
- DGX: `~/teacher-lessons/read/` (archive)
