# hitcc-claude-code-reverse-engineering

*Researched: 2026-04-01 22:51 CDT*

# HitCC — Claude Code Reverse-Engineering Documentation

**Source:** [hitmux/HitCC](https://github.com/hitmux/HitCC) (★646, CC-BY 4.0)

## Overview
Complete reverse-engineering of Claude Code CLI v2.1.84 Node.js version. 81 files, 27,170 lines, 698K chars of documentation. Not source code — a structured knowledge base for understanding how Claude Code works internally.

## Documentation Structure

### 00-overview — Scope, evidence sources, confidence terminology
### 01-runtime — The core agent loop
- **01**: Product CLI and modes
- **02**: Session and persistence
- **03**: Input compilation pipeline
- **04**: Agent loop and compaction (4 sub-pages)
  - Main loop state, caches, and yield surface
  - Compaction pipeline and auto-compact tracking
  - No-tool branch: recovery, stop, and reactive compact
  - Tool round: next turn and terminal reasons
- **05**: Model adapter, provider selection, auth
- **06**: Stream processing and remote transport
- **07-08**: Web search and web fetch built-in tools
- **09**: API lifecycle and telemetry
- **10**: Control plane API and auxiliary services
- **11**: Non-LLM network paths
- **12**: Settings and configuration system

### 02-execution — Tools, hooks, and permissions
### 03-ecosystem — TUI system, MCP, plugins, skills
### 04-rewrite — Architecture for reimplementation
### 05-appendix — Supplementary details

## Key Agent Loop Findings

### TurnState (`J`) — The core state object
```typescript
interface TurnState {
  messages: TranscriptLikeMessage[]
  toolUseContext: ToolUseContext
  maxOutputTokensOverride?: number
  autoCompactTracking?: {
    compacted: boolean
    turnId: string
    turnCounter: number
    consecutiveFailures?: number
  }
  stopHookActive?: boolean
  maxOutputTokensRecoveryCount: number
  hasAttemptedReactiveCompact: boolean
  turnCount: number
  pendingToolUseSummary?: Promise<TranscriptLikeMessage | null> | null
  transition?: { reason: string; [k: string]: unknown }
}
```

### Main Loop Pseudocode
```
J = initialTurnState(input)
while (true):
  F = normalize(messages)
  F = applyContentReplacement(F)
  F = microcompact(F)
  
  { compactionResult, consecutiveFailures } = autocompact(F, cache, tracking)
  if compacted:
    yield compact boundary / summary / attachments
    F = compacted transcript
  
  for await event from callModel(...):
    yield raw stream_event + assistant fragments + partial tool results
    accumulate M6 / $6 / T6 / z6
  
  if no tool_use:
    handle reactive compact / max_output_tokens / stop hooks / completed
  else:
    execute tools
    emit attachments / queued commands / skill artifacts
    rewrite J for next turn and continue
```

### Key Patterns
1. **Microcompact**: Every turn applies microcompact to normalize messages before sending
2. **Auto-compact tracking**: Tracks consecutive compaction failures with circuit breaker
3. **Reactive compact**: When model output hits max tokens, triggers emergency compaction and retries
4. **Tool Use Summary**: Tool results are processed asynchronously and fed back as pending promises
5. **Stop hooks**: External systems can inject stop conditions into the agent loop

## Relevance to SOMA
1. **Agent loop design**: Hermes uses a similar loop but without microcompact. We should add pre-turn message normalization.
2. **Compaction strategy**: Claude Code has 4 compaction levels (micro, partial, full, session-memory). Hermes only has one.
3. **Turn state management**: The J object pattern (wholesale replacement vs mutation) is cleaner than what Hermes does.
4. **Tool result promises**: The async tool summary pattern avoids blocking the main loop.


## Sources

- https://github.com/hitmux/HitCC
