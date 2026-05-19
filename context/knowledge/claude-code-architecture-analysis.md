# claude-code-architecture-analysis

*Researched: 2026-03-31 16:42 CDT*

# Claude Code Architecture Analysis (from instructkr/claw-code)

## System Prompt Architecture

### Layered Prompt Construction
Claude Code builds its system prompt in 11 ordered sections:
1. **Intro** - Role definition + URL safety rule
2. **Output Style** (optional) - Pluggable response persona
3. **System Rules** - Tool execution context, system reminders, compaction awareness
4. **Doing Tasks** - Scoped changes, no speculative abstractions, diagnose before pivoting
5. **Executing Actions with Care** - Reversibility vs blast radius framing
6. **Dynamic Boundary Marker** - `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` for prompt caching
7. **Environment Context** - Model family, cwd, date, OS
8. **Project Context** - Git status snapshot
9. **CLAUDE.md Instructions** - Hierarchical (root-to-leaf), walks up to filesystem root
10. **Runtime Config** - Merged user/project/local settings
11. **Appended Sections** - Custom additions

### Key Prompt Engineering Techniques
- "If an approach fails, diagnose the failure before switching tactics"
- "Read relevant code before changing it and keep changes tightly scoped"
- "Do not add speculative abstractions, compatibility shims, or unrelated cleanup"
- "Report outcomes faithfully: if verification fails or was not run, say so explicitly"
- Blast radius awareness: local/reversible OK, shared/destructive needs authorization
- After compaction: "Resume directly -- do not acknowledge the summary, do not recap"

## Tool Architecture
- 6 tools: bash, read_file, write_file, edit_file, glob_search, grep_search
- All schemas use `"additionalProperties": false` for strictness
- Tool dispatch: match on name -> deserialize to typed struct -> execute -> Result<String, String>
- Bash: `sh -lc` (login shell), timeout support, background mode
- edit_file: exact string match (no fuzzy), replace_all option
- Patch format: simple +/- line diff (not unified diff)

## Context Compaction
- Sliding window: preserve last 4 messages verbatim
- Trigger: message count > 4 AND estimated tokens >= 10,000
- Token estimation: chars/4 + 1 per block (cheap heuristic)
- Summary: role-labeled, block-type-aware, truncated to 160 chars per block
- Strips `<analysis>` tags, keeps `<summary>` content
- Continuation message: "Resume directly without acknowledging"

## Session Persistence
- Flat append-only log: Vec<ConversationMessage> serialized as JSON
- No separate metadata - entire conversation is one file
- Usage tracking reconstructed by scanning message history

## Permission Model
- Three modes: Allow, Deny, Prompt
- Per-tool overrides via config
- Denied tools produce error tool results fed back to model

## What Hermes Can Adopt
1. Structured system prompt sections with caching boundary
2. Compaction: sliding window + structured summary (160-char truncation)
3. "Diagnose before pivoting" as a core instruction
4. Blast radius awareness for tool use
5. Hierarchical instruction files (CLAUDE.md pattern)
6. Post-compaction "resume directly" continuation
7. Strict tool schemas with additionalProperties: false


## Sources

- https://github.com/instructkr/claw-code
