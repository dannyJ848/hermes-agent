---
name: claude-code-patterns
description: Techniques extracted from Claude Code source for improving agent prompt engineering and context management
version: 1
---

# Claude Code Patterns for Better Agent Performance

## Prompt Engineering Tricks (from prompt.rs)

### "Diagnose Before Pivoting"
When an approach fails, explicitly instruct the agent to debug/understand WHY it failed before trying something different. This prevents the "flail" pattern where agents try 10 random approaches.

### Blast Radius Awareness
Teach the agent to categorize actions:
- **Local + reversible** (file edits, test runs) = just do it
- **Shared/destructive** (deploys, deletes, publishes) = needs explicit authorization

### Scope Control Rules
- "Read relevant code before changing it"
- "Keep changes tightly scoped to the request"
- "Do not add speculative abstractions"
- "Do not create files unless required"
- "Do not add compatibility shims or unrelated cleanup"

### Post-Compaction Continuation
After context compaction, tell the agent:
"Resume directly -- do not acknowledge the summary, do not recap what was happening, and do not preface with continuation text."

This prevents wasted tokens on "I see we were working on..."

## Context Management (from compact.rs)

### Sliding Window + Summary
- Keep last N messages verbatim (default: 4)
- Summarize older messages with role labels
- Truncate each block to 160 chars
- Strip internal reasoning (<analysis> tags)
- Preserve summary content only

### Token Estimation
Simple heuristic: `text.length / 4 + 1` per block. Good enough for triggering compaction without needing a real tokenizer.

### Compaction Trigger
```
messages.length > preserveCount && estimatedTokens >= maxTokens
```

## Tool Design (from tools/src/lib.rs)

### Strict Schemas
All tool schemas should use `"additionalProperties": false`. This prevents the LLM from hallucinating parameters.

### Error Handling
Tools return `Result<String, String>` - errors are always human-readable strings that the model can understand and act on.

### Bash Safety
- Use login shell (`sh -lc`) for proper env loading
- Timeout support is essential
- Background mode for long-running processes

## System Prompt Structure (from prompt.rs)

### Ordered Sections
1. Role definition + safety rules
2. Optional persona/style
3. System-level rules (tool context, compaction awareness)
4. Task execution guidelines
5. Safety/blast radius section
6. **Dynamic boundary** (for caching)
7. Environment context (model, cwd, date, OS)
8. Project context (git status)
9. Hierarchical instructions (CLAUDE.md pattern)
10. Merged runtime config

### Dynamic Boundary Marker
Insert a separator between static and dynamic prompt sections. The static prefix can be cached by the API provider, saving input tokens on every request.

### Hierarchical Instructions
Walk from filesystem root to cwd, collecting instruction files at each level. Load in ancestor-to-descendant order (root first, closest last). This enables project-specific overrides without losing general instructions.
