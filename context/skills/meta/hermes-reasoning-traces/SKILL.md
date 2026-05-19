---
name: hermes-reasoning-traces
description: Patterns extracted from the Lambda/NousResearch Hermes Agent Reasoning Traces dataset (Kimi K2.5, 7,646 examples, ~150M tokens). Use these patterns to improve tool-calling and reasoning quality.
version: 1.0
category: meta
tags: [reasoning, tool-calling, hermes, kimi, patterns]
---

# Hermes Agent Reasoning Traces - Integrated Patterns

**Source:** [lambda/hermes-agent-reasoning-traces](https://huggingface.co/datasets/lambda/hermes-agent-reasoning-traces)
**Model:** Kimi K2.5 | **License:** Apache 2.0 | **Date:** April 2026

## Dataset Overview
- 7,646 examples, ~150M tokens
- Categories: Terminal & Coding (26%), Agent Tools (19%), Browser Automation (14%), Multi-Tool (11%)
- Format: ShareGPT with `<think` reasoning, `<tool_call` invocations, `<tool_response` results

## Core Behavioral Rules

### 1. VERIFY-AFTER-WRITE (29% baseline)
After every `write_file` or `patch`, immediately verify:
- Use `terminal` to run build/lint/test
- Use `read_file` to confirm file content
- The top agents verify 29% of the time — match or exceed this

### 2. ITERATIVE REFINEMENT IS KING
- `terminal -> terminal` is the #1 tool sequence (1,081 occurrences)
- `write_file -> write_file` is #2 (590 occurrences)
- Agents rarely get it right first try — iterate rapidly

### 3. CONCISE REASONING (145 char median)
- Average thinking block: 276 chars
- Median: 145 chars
- Pattern: observe -> decide -> act. No lengthy self-reflection.

### 4. ERROR RECOVERY (33% of tasks)
- 1 in 3 tasks involves error recovery thinking
- Key phrases: "that didn't work", "try a different approach", "alternative"
- When stuck, pivot strategy rather than retry identically

### 5. PLAN-THEN-EXECUTE (for complex tasks)
- 6.4% of thinking blocks contain planning
- Pattern: "Let me start by... then..."
- Correlates with success on 15+ tool-call tasks

### 6. OBSERVATION-DRIVEN CHAINING
- 7.1% of thinking starts with "based on the output..."
- Always reference previous tool output before deciding next action
- Don't make assumptions — read the actual data

## Tool Sequence Patterns (Top 10)
| Sequence | Count | Use Case |
|----------|-------|----------|
| terminal -> terminal | 1,081 | Iterative debugging/execution |
| write_file -> write_file | 590 | Batch file creation |
| terminal -> write_file | 215 | Explore then create |
| write_file -> terminal | 212 | Create then verify |
| read_file -> read_file | 203 | Deep investigation |
| search_files -> search_files | 170 | Broad search |
| terminal -> read_file | 140 | Execute then inspect |
| search_files -> terminal | 125 | Search then act |
| read_file -> terminal | 108 | Read then execute |
| browser_navigate -> browser_snapshot | 69 | Browser exploration |

## Anti-Patterns to Avoid
1. **Never verify with the patch tool's lint checker** — it uses stale TS config. Use `npx tsc --noEmit`.
2. **Don't call tools without thinking first** — even 145 chars of reasoning improves outcomes.
3. **Don't retry identically on failure** — pivot approach (2.1% of traces show successful pivots).

## Local Dataset
- Downloaded to `/tmp/hermes_traces.parquet` (485MB)
- Load with: `pd.read_parquet('/tmp/hermes_traces.parquet')`
