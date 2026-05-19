---
name: squad-dev
description: Spawn a coordinated team of parallel Hermes subagents for code work. Battle-tested with 8 consecutive autonomous sprints (Sprints 1-8, all green).
version: 3.0
created: 2026-03-31
updated: 2026-03-31
---

# Squad Development

Spawns up to 3 parallel `delegate_task` subagents for concurrent code fixes.

## Critical Lessons (Learned the Hard Way)

### Sprint #1 FAILED -- agents only read files, never wrote code
- **Cause**: Context was too long (~500 words per agent). Agents burned their entire iteration budget (50 tool calls) reading files and searching, then got interrupted at the 200s timeout before making any patches.
- **Fix for Sprint #2**: Cut context to ~200 words. Put the ROOT CAUSE HYPOTHESIS right in the context so agents don't spend 30 calls searching for it. Specify exact line numbers. Result: all 3 agents completed with fixes.

### What actually matters:
1. **Short, targeted context** -- under 200 words. Give the answer, not the investigation.
2. **Explicit file ownership** -- tell each agent which files they CAN and CANNOT touch.
3. **Root cause hint** -- don't make agents figure it out; tell them your best guess.
4. **Line numbers** -- give approximate line numbers for key code sections.

### What doesn't matter:
- The shared message board -- agents didn't use it in practice. Each works in isolation and returns a summary. Coordination happens through file ownership, not inter-agent messages.
- File locking -- not needed if you give each agent exclusive file ownership upfront.

## How to Use

### Step 1: Partition the work

Split bugs/features into independent tasks with ZERO file overlap:
```
Agent A: files [foo.tsx, bar.ts] -- owns these exclusively
Agent B: files [baz.tsx] -- owns this exclusively
Agent C: files [styles.css, config.ts] -- owns these exclusively
```

### Step 2: Write tight agent context

BAD (Sprint #1 style -- too vague, agent investigates forever):
```
"Fix the WebGL crash. The app shows 'Vista 3D No Disponible' when clicking body regions.
Investigate AnatomyViewer.tsx, EnhancedAnatomyModel.tsx, and AnatomyStructures.ts.
Find the root cause and fix it."
```

GOOD (Sprint #2 style -- targeted, agent fixes fast):
```
"Fix WebGL crash on body region click.
FILE: src/AnatomyViewer.tsx only.
ROOT CAUSE: Clicking sets React state which causes re-render. Suspense wrapper around
Canvas replaces it with loading screen on re-render, destroying WebGL context.
FIX: Remove Suspense wrapper from Canvas (lines ~1789-1790). Memoize gl/style/onCreated
props with useMemo/useCallback to prevent unnecessary Canvas reconfiguration.
Lines 585-605: click handlers. Lines 1790: Canvas element.
Use patch tool only."
```

### Step 3: Spawn with delegate_task

```
delegate_task(tasks=[
  { goal: "<1 line summary>", context: "<200 word targeted context>", toolsets: ["terminal", "file"] },
  ...up to 3 agents
])
```

### Step 4: Verify after completion

1. `npx tsc --noEmit` -- check for type errors introduced by parallel edits
2. `npx vite build` -- verify build still works
3. Read agent summaries for what was actually changed
4. If conflicts exist (shouldn't if file ownership was clean), resolve manually

## Agent Context Template

```
PROJECT: /path/to/project
BUG: <1 sentence description>
FILE: <exact file path> (only edit this file)
ROOT CAUSE: <your best guess at the cause>
FIX: <specific action to take>
KEY LINES: <approximate line numbers>
DO NOT TOUCH: <list files owned by other agents>
Use patch tool only. NOT write_file.
```

## Limits
- Max 3 concurrent agents (delegate_task hard limit)
- ~50 tool calls per agent before max_iterations
- ~900s before timeout (varies by model)
- Each agent gets isolated terminal/cwd
- Agents cannot communicate with each other directly
- Only final summaries return to orchestrator

## Autonomous Sprint Loop (24h Mode)

For fully autonomous development over extended periods:

### Loop Pattern
```
1. Assess remaining work (bugs, features, audit items)
2. Partition into 2-3 independent tasks with ZERO file overlap
3. delegate_task(tasks=[...]) -- spawn squad
4. Verify build: npx tsc --noEmit (fix any errors yourself)
5. Send Telegram update (via notify script or telegram_card)
6. Immediately start next sprint -- DO NOT WAIT for user
7. Update DEVPLAN.md with completed items
8. Repeat until all work done or user interrupts
```

### Sprint Frequency
- Each sprint takes ~5-15 minutes (subagent parallel execution)
- 6-8 sprints per hour possible
- Cron dev-loop (every 2h) handles continuation across sessions
- Cron progress-report (every 4h) sends Telegram summaries

### What to tackle per sprint (priority order):
1. Critical bugs first (crashes, blank screens, broken navigation)
2. i18n / hardcoded strings (easy wins, agents handle well)
3. Missing mocks / stubs (browser mode needs full mock coverage)
4. New features (data layers, UI components, mappings)
5. Visual polish (CSS animations, hover states, transitions)
6. Content (encyclopedia entries, translations)

### Telegram Notification Pattern
```python
python3 << 'PYEOF'
import sys; sys.path.insert(0, '/tmp')
from soma_notify import send_card
send_card('Sprint Title', 'Summary of what was done', 'success')
PYEOF
```

### Common Agent Failure Modes (8-sprint observations)
- **Timeout on read_file**: Network flakiness. Retry the same task or do it yourself.
- **write_file instead of patch**: Agents sometimes use write_file which corrupts. Always specify "Use patch tool only" in context.
- **React.useEffect instead of useEffect**: When agent creates new components, it may use React. prefix. Fix manually.
- **Circular i18n imports**: If agent adds t() to a file that doesn't import useTranslation, build breaks. Always verify.

### Typical Sprint Yield
- Bug fixes: 2-4 bugs per sprint
- i18n: 15-30 strings per sprint
- New features: 1 feature per sprint (data layer + integration)
- CSS polish: 5-10 animation/style improvements per sprint

## When NOT to use squad-dev
- Tasks share files (use single agent instead)
- Tasks depend on each other's output (run sequentially)
- Changes are simple (single tool call -- do it yourself)
- You need visual/browser verification (agents can't do this)
- Network is flaky (timeouts waste the whole sprint -- do it yourself)
