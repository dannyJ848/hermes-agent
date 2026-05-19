---
name: master-agent-playbook
description: Synthesis of techniques from Claude Code, OpenHands, SWE-agent, Aider, ReAct, Reflexion, LATS, Tree-of-Thought, Self-Refine, and Plan-and-Solve. The definitive guide to being a sharper, faster AI agent.
version: 3
---

# Master Agent Playbook

Compiled from analysis of 10 agent systems + 6 academic frameworks.

---

## SECTION 1: CORE REASONING PATTERNS

### 1.1 ReAct Loop (Interleaved Reasoning + Acting)
Every task step follows: THOUGHT -> ACTION -> OBSERVATION

```
Thought: [Reason about current state, what to do next, why]
Action: [Execute a tool call]
Observation: [Process the result]
Thought: [Update plan based on observation]
```

Rules:
- Always think BEFORE acting. Never fire a tool call without a reasoning trace.
- Observations must update your mental model. If the result contradicts your assumption, acknowledge it and adjust.
- Ground reasoning in actual data (file contents, error messages), not speculation.

### 1.2 Plan-and-Solve Decomposition
For complex tasks, explicitly decompose BEFORE executing:

```
Step 1: Understand the problem (read relevant code/files)
Step 2: Identify sub-problems
Step 3: Order sub-problems by dependency
Step 4: Execute each sub-problem with ReAct
Step 5: Verify the whole solution works
```

Rules:
- NEVER start implementing before understanding the full scope. Read first.
- If a task has 3+ steps, write them down before starting.
- Dependencies matter -- don't build on top of code you haven't read yet.

### 1.3 Diagnose Before Pivoting (from Claude Code)
When something fails:
1. Read the error message CAREFULLY. Every word matters.
2. Identify the ROOT CAUSE, not just the symptom.
3. Form a hypothesis about why it failed.
4. Test the hypothesis with a minimal change.
5. Only THEN try a different approach if the hypothesis was wrong.

Anti-patterns:
- Trying 5 different approaches without understanding why each failed
- Copy-pasting Stack Overflow solutions without reading the code
- "Let me try X instead" without explaining WHY X might work better

---

## SECTION 2: CONTEXT MANAGEMENT

### 2.1 Sliding Window + Structured Summary (from Claude Code)
- Keep last 4 exchanges verbatim (full detail preserved)
- Older content: summarize with role labels, truncate each block to 160 chars
- Strip internal reasoning (analysis blocks), keep only conclusions
- After compaction: "Resume directly, do not acknowledge the summary"

### 2.2 Repo Map Pattern (from Aider)
- Use PageRank over code definition/reference graph to identify important files
- Binary search over token budget for optimal context compression
- Prioritize: config files > entry points > core modules > utilities
- Mentioned files get higher priority than unmentioned files

### 2.3 Composable History Processors (from SWE-agent)
Pipeline of transforms applied to conversation history:
1. LastN: Keep only last N observations, replace older with "N lines omitted"
2. ClosedWindow: For file views, keep only most recent window per file
3. CacheControl: Add cache markers to frequently-sent messages
4. RemoveRegex: Strip diff output and other noise from history

### 2.4 Structured Summary Condensation (from OpenHands)
Use structured output (Pydantic/JSON schema) to produce state summaries:
```json
{
  "completed_tasks": ["..."],
  "pending_tasks": ["..."],
  "files_modified": ["..."],
  "error_messages": ["..."],
  "current_state": "..."
}
```
This is more reliable than free-text summaries for maintaining agent state.

---

## SECTION 3: ERROR RECOVERY

### 3.1 Stuck Detection (from OpenHands)
Detect 5 stuck patterns:
1. **Repeating action+observation**: Last 4 actions AND observations are identical
2. **Repeating action+error**: Last 3 actions identical, all errors
3. **Repeating syntax errors**: Same syntax error on same line 3 times
4. **Monologue loop**: 3 identical agent messages with no tool use
5. **A-B pattern**: 6 consecutive actions alternating between exactly 2 states

Recovery: Roll back to before the loop, add a reflection on what went wrong.

### 3.2 Reflexion Pattern (from Shinn et al.)
After a failed attempt:
1. Generate a verbal self-reflection: "What went wrong and how should I change?"
2. Store the reflection in episodic memory
3. On next attempt, include accumulated reflections as context
4. Keep max 3 reflections (older ones get dropped)

### 3.3 Exponential Backoff with Retry (from Claude Code API)
- 200ms initial delay, 2s max, 2 retries (3 total attempts)
- Retryable: timeouts, 408, 429, 500, 502, 503, 504
- Non-retryable errors: return immediately
- Backoff: `delay = min(200ms << (attempt-1), 2000ms)`

### 3.4 Error Taxonomy (from Claude Code)
Classify errors to choose the right response:
- **Recoverable**: Tool timeout, API rate limit -> retry with backoff
- **Fixable**: Type error, missing file -> diagnose and fix the input
- **Fundamental**: Wrong approach -> step back, reflect, try different strategy
- **Fatal**: Permission denied, out of memory -> report to user, ask for help

---

## SECTION 4: SELF-EVALUATION

### 4.1 Self-Refine Loop (from Madaan et al.)
```
OUTPUT -> EVALUATE -> REFINE -> OUTPUT' -> EVALUATE -> ... -> FINAL
```
1. Generate initial output
2. Evaluate against criteria (correctness, completeness, style)
3. Generate specific feedback
4. Produce refined output incorporating feedback
5. Repeat up to 3 rounds or until quality threshold met

### 4.2 Tree-of-Thought Branching (from Yao et al.)
For high-stakes decisions:
1. Generate 3-5 possible approaches
2. Evaluate each approach's expected outcome
3. Select the most promising branch
4. If stuck, backtrack to a previous decision point
5. Breadth-first for exploration, depth-first for execution

### 4.3 Auto-Verify Pipeline (from Aider)
After every code change:
1. Run linter on modified files
2. Run relevant tests
3. If failures: analyze, fix, re-run (up to 3 rounds)
4. Report final state honestly (pass/fail/not run)

---

## SECTION 5: MULTI-AGENT COORDINATION

### 5.1 Architect/Editor Split (from Aider)
- **Architect** (strong model): Plans changes, identifies files, designs approach
- **Editor** (fast model): Implements specific changes following the plan
- Separation of planning from execution improves both quality and cost

### 5.2 Action Sampling (from SWE-agent)
For uncertain tasks, generate multiple solutions:
- **AskColleagues**: N models propose solutions in parallel, choose best
- **Tournament**: Pairwise compare solutions, bracket-style elimination
- **Best-of-N**: Generate N solutions, score each, pick highest

### 5.3 Delegation Best Practices
When delegating to sub-agents:
1. Provide ALL context they need (they have no memory of your conversation)
2. Specify the exact file paths, not just "the seed file"
3. Give success criteria (what does "done" look like?)
4. Include constraints (don't refactor, don't change X, use patch not write_file)
5. Set explicit scope (only fix X, nothing else)

---

## SECTION 6: PROMPT ENGINEERING

### 6.1 Layered System Prompt (from Claude Code)
Build prompts in ordered sections:
1. Role definition + safety rules
2. Optional persona/style override
3. System rules (tool context, compaction awareness)
4. Task execution guidelines
5. Safety/blast radius section
6. **Dynamic boundary** (cache everything above this)
7. Environment context (model, cwd, date, OS)
8. Project context (git status)
9. Hierarchical instructions (root-to-leaf CLAUDE.md files)
10. Merged runtime config

### 6.2 Scope Control Instructions (from Claude Code)
Include these in your system prompt:
- "Read relevant code before changing it"
- "Keep changes tightly scoped to the request"
- "Do not add speculative abstractions"
- "Do not create files unless required"
- "Report outcomes faithfully"

### 6.3 Cost Awareness (from OpenHands)
- "Each action you take is somewhat expensive"
- "Combine multiple operations into a single action when possible"
- "Read files once, not repeatedly"
- "Plan before executing to minimize wasted actions"

### 6.4 Post-Compaction Continuation (from Claude Code)
After any context reset/compaction:
"Resume directly -- do not acknowledge the summary, do not recap what was happening, and do not preface with continuation text."

This saves 100-200 tokens of wasted acknowledgment per compaction.

---

## SECTION 7: TOOL DESIGN PRINCIPLES

### 7.1 Minimal Tool Set (from Claude Code)
6 tools is enough: bash, read_file, write_file, edit_file, glob_search, grep_search.
- More tools = more confusion = worse tool selection
- Fewer, more powerful tools = better agent performance
- Each tool should be orthogonal (no overlapping functionality)

### 7.2 Strict Schemas (from Claude Code)
All tool schemas: `additionalProperties: false`
- Prevents hallucinated parameters
- Forces the model to use only what's documented
- Clear error messages when model tries invalid params

### 7.3 Error Messages as Feedback (from Claude Code)
- Tool errors are always human-readable strings
- Errors are fed back as tool results (not hidden)
- Model sees the error and can self-correct within the same turn
- Permission denials become tool errors too: "tool X denied by policy"

---

## SECTION 8: BLAST RADIUS AWARENESS (from Claude Code)

Before any action, evaluate:
- **Local + Reversible** (file edits, test runs) -> Just do it
- **Local + Irreversible** (delete files, force push) -> Confirm with user
- **Shared + Reversible** (edit shared config) -> Coordinate with team
- **Shared + Irreversible** (deploy to prod, drop database) -> Explicit authorization required

---

## QUICK REFERENCE: BEHAVIORAL RULES

1. **Think before acting** -- always have a reasoning trace before tool calls
2. **Read before writing** -- understand existing code before changing it
3. **Diagnose before pivoting** -- understand failures before trying alternatives
4. **Keep changes scoped** -- no speculative abstractions or drive-by refactors
5. **Verify after implementing** -- run linters, tests, type checks
6. **Reflect on failures** -- verbal self-reflection on what went wrong
7. **Combine operations** -- minimize total actions by batching
8. **Resume directly** -- after context resets, don't waste tokens on recap
9. **Evaluate blast radius** -- reversible is fine, irreversible needs authorization
10. **Report honestly** -- if verification wasn't run or failed, say so explicitly
