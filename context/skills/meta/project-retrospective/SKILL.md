---
name: project-retrospective
version: 1.0
description: "Post-project reflection methodology. Gathers multi-session history, structures successes/failures/patterns, distills into training gym tips, skill patches, and new modules."
trigger: "After completing a multi-session project (3+ sessions), or when the user asks to reflect on past work"
---

# Project Retrospective Methodology

## When to Use
- After completing a project that spanned 3+ sessions
- When the user asks "what did we learn from X project?"
- During self-improvement cycles when reviewing past work
- When transitioning from a completed project to the next phase

## Step-by-Step Process

### Step 1: Gather Full Project History
- Use `session_search` with multiple queries covering the project's key terms
- Don't rely on a single query — use 3-5 queries with different keywords (project name, tools used, errors encountered, key files)
- Reconstruct the timeline: when did each session happen, what was accomplished, where did it fail
- Load any relevant skills that were created/used during the project

### Step 2: Structure the Reflection
Write a structured markdown document with these sections:

1. **PROJECT SCOPE** — what was the goal, what phases existed, final metrics
2. **WHAT WORKED (Successes)** — numbered list with S-prefix, each with the insight and WHY it worked
3. **WHAT FAILED (Pain Points)** — numbered list with F-prefix, each with root cause and fix applied
4. **PATTERNS (Cross-Cutting)** — numbered list with P-prefix, insights that span multiple failures/successes
5. **QUANTITATIVE SUMMARY** — table of key metrics
6. **WHAT TO BUILD DIFFERENTLY** — numbered list of concrete changes for next time

Save this to `/tmp/{project_name}_reflection.md` for reference.

### Step 3: Distill into Training Gym Tips
- Extract 5-10 actionable tips from the reflection (NOT just observations — must be DO/AVOID directives)
- Each tip needs: condition (WHEN...), recommendation (DO...), rationale (because...), source
- Insert into Cortex via `CortexDB.insert_node()` with node_type="tip"
- Use the reflection document to ensure tips are grounded in specific failures/successes, not speculation

### Step 4: Patch Existing Skills
- For each skill used during the project, check if the reflection reveals gaps or outdated info
- Use `skill_manage(action='patch')` to add new sections:
  - "Reflection Lessons" section for insights
  - New pitfalls discovered
  - Updated known errors/fixes
- Focus on WHAT WOULD HAVE HELPED during the project — if a skill had contained insight X, would it have saved time?

### Step 5: Build New Modules (if warranted)
- If the reflection reveals a gap that no existing tool/skill fills, build a new module
- Write to `~/subconscious/{module_name}.py`
- Test standalone before wiring into the plugin
- The module should directly address a specific failure from the reflection

### Step 6: Save Finding
- Use `save_finding()` to persist the full reflection to the knowledge library
- Include source session IDs for traceability

### Step 7: Update Memory
- Record key decisions and their rationale in memory (not just outcomes)
- This prevents re-litigating decisions in future sessions

## Pitfalls
- Don't produce tips that are too vague ("be careful with APIs") — must be specific and actionable
- Don't skip Step 1 (gathering history) — you WILL miss important context from earlier sessions
- Don't only focus on failures — successes encode patterns worth reinforcing
- Don't skip the "build new module" step if a clear gap exists — tips without implementation is hoarding
- When searching sessions, use OR between keywords (FTS5 defaults to AND which misses partial matches)
- `session_search` with `limit=5` is usually enough — but for 5+ session projects, may need multiple searches

## Example Output (from UWorld Project Retrospective, Apr 2026)
- Reflection: /tmp/uworld_project_reflection.md (8.9KB)
- Tips inserted: 10 into Cortex (silent_failure_detection, api_safety, batch_safety, filter_verification, etc.)
- Skill patched: uworld-api-extraction (added Reflection Lessons section)
- Module built: ~/subconscious/api_type_validator.py (catches silent type mismatches)
- Finding saved: uworld-project-full-reflection-apr2026
