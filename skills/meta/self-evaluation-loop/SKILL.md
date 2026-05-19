---
name: self-evaluation-loop
description: Apply the Self-Refine + Reflexion pattern to improve output quality before delivering results
version: 1
---

# Self-Evaluation Loop

Based on Self-Refine (Madaan et al.) + Reflexion (Shinn et al.) + Auto-Verify (Aider).

## When to Use
- After completing a non-trivial task (5+ tool calls)
- Before delivering research summaries
- After writing or editing significant code
- When the task has clear success criteria

## The Loop

### Step 1: Generate Initial Output
Complete the task normally.

### Step 2: Self-Evaluate
Ask yourself these questions:
- Does the output fully address the original request?
- Are there any factual errors or hallucinations?
- Is the code/test change correct and complete?
- Were all constraints respected?
- Score 1-10 on completeness, accuracy, and quality

### Step 3: Identify Gaps
List specific improvements needed:
- Missing information
- Incorrect assumptions
- Scope creep or missed scope
- Style/formatting issues

### Step 4: Refine (1-2 rounds max)
- Make targeted improvements
- Re-evaluate
- Stop when score >= 8/10 or max rounds reached

### Step 5: Report Honestly
- What was accomplished
- What wasn't done (and why)
- Confidence level (high/medium/low)
- What should be verified by a human

## For Code Tasks specifically:
After every code change:
1. Run linter (tsc, eslint, etc.)
2. Run tests if they exist
3. Check that the change is minimal and scoped
4. Verify no unrelated files were touched

## For Research Tasks specifically:
After producing a research summary:
1. Check: Did I answer the specific question asked?
2. Check: Are claims backed by sources?
3. Check: Is the summary actionable?
4. Check: Are there obvious gaps in coverage?

## Failure Reflection (Reflexion Pattern)
When a task fails completely:
1. Generate a verbal reflection: "What went wrong and how should I change?"
2. Save the reflection to learnings
3. On similar future tasks, check past reflections first
