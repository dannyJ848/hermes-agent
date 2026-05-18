---
name: degraded-mode-autonomous-operation
description: Continue productive autonomous work when terminal/execute_code are completely broken. Maps each phase of the autonomous cycle to working alternatives so no cycle is wasted.
version: 1.0
---

# Degraded-Mode Autonomous Operation

## When to Use
When terminal and execute_code both return SIGSEGV (exit code -11) or are otherwise completely unavailable. This is different from a single tool failure — it's a **systemic infrastructure failure** affecting all code execution paths.

## Diagnosis
- Terminal returns `exit_code: -11` (SIGSEGV) on EVERY command, including `echo hello`
- execute_code also crashes with SIGSEGV
- The sandbox/container runtime is broken, not individual tools

## Tool Availability Map (Degraded Mode)

### WORKING (use as replacements):
| Normal Tool | Degraded Replacement | What It Does |
|-------------|---------------------|--------------|
| terminal (shell commands) | web_research + web_extract | Research instead of run scripts |
| execute_code (Python) | save_finding | Save results via knowledge tools |
| domain_certainty.py | web_research on trending topics | Pick research target manually |
| meta_loop.py | session_search + memory_score | Review recent work |
| research_to_distillation.py | Manual save_finding + skill_manage | Save findings directly |
| tool_planner.py | skill_view existing skills | Review capability via knowledge |
| cerebrum DB queries | status_check + cost_check | Get system stats from APIs |
| Git operations | web_extract GitHub URLs | Read repos via web instead of clone |

### STILL WORKING (usually):
- web_research, web_extract, web_search
- save_finding (knowledge base writes)
- session_search, session_checkpoint, session_restore
- status_check, cost_check
- evey_goals
- skill_view, skill_manage, skills_list

### SOMETIMES BROKEN (test before relying):
- memory, memory_score, memory_decay — may return "Memory is not available" even in degraded mode
- knowledge_search, knowledge_stats — depends on Qdrant/vector DB state
- If memory is down, skip memory maintenance and focus on research + save_finding
- knowledge_search, knowledge_stats
- autonomous_decide, autonomous_plan, autonomous_reflect
- cronjob (list/check only — don't create new jobs)
- watchdog_heartbeat, watchdog_status
- send_message, telegram_card, telegram_status
- read_file, write_file, patch, search_files

### BROKEN (all terminal-dependent):
- terminal, process, execute_code
- Any ~/subconscious/*.py scripts
- cerebrum_memory.db direct queries
- Git operations, npm, python commands
- Docker, cloudflared, server management

## Phase Mapping for Autonomous Cycles

When the standard 6-phase cycle scripts are unavailable:

| Phase | Normal | Degraded Alternative |
|-------|--------|---------------------|
| 1. Domain Certainty | domain_certainty.py | Use time-of-day bias from autonomous-curiosity + recent session_search results |
| 2. Meta-Loop | meta_loop.py | Review session_search for recent work, check memory_score for stale memories |
| 3. Targeted Research | (web tools work fine) | web_research → web_extract → save_finding — full pipeline available |
| 4. Distillation | research_to_distillation.py | save_finding directly, or skill_manage for behavioral tips |
| 5. Capability Check | tool_planner.py | skill_view relevant skills to review current capability |
| 6. KG Stats | cerebrum DB query | Use `knowledge_stats` tool — returns node/edge/tip counts without needing terminal. Partial but useful. |

## Workflow (Step by Step)

1. **Detect:** Run `echo hello` in terminal. If SIGSEGV → degraded mode.
2. **Classify:** Try execute_code with a trivial script. If also SIGSEGV → full degraded mode.
3. **Adapt:** Use the tool map above. Prioritize research (web tools still work).
4. **Research:** This is the most productive activity in degraded mode. Run 2-3 web_research queries, extract best results, save findings.
5. **Memory:** Use memory tool to note the infrastructure issue. Use memory_decay/memory_score for maintenance.
6. **Skills:** Review and patch existing skills (skill_view + skill_manage).
7. **Report:** Output honest summary noting which phases completed and which couldn't run.
8. **Exit:** Use [SILENT] if nothing meaningful to report. Don't force tool calls on broken infrastructure.

## Key Insight
**Research productivity is nearly unaffected by terminal failure.** The web_research → web_extract → save_finding pipeline is the highest-value autonomous activity and requires zero terminal access. A degraded cycle should still produce 2-3 research findings.

## web_extract 403 Fallback
When `web_extract` returns HTTP 403 Forbidden (common on MDPI, some publisher sites):
- **Don't retry the same URL** — it will keep returning 403
- **Switch to web_research** for the same topic and pick an alternative source
- **Accept partial content** — if a site blocks full extraction, the search snippet often has enough key info
- This pattern works: `web_research(topic)` → extract top 2-3 URLs → `web_extract` each → if 403, skip to next URL

## Pitfalls
- Don't waste 5+ terminal calls confirming it's broken — 2 failures (simple + complex) is enough to declare degraded mode
- Don't try to "fix" the terminal from inside the broken sandbox — it needs external intervention
- Don't skip the cycle entirely — research and memory maintenance don't need terminal
- Don't forget to note the infrastructure issue so the next cycle (or V) knows about it

## Recovery
Terminal SIGSEGV typically requires:
- Container/sandbox restart (external action)
- VPS reboot if persistent
- Check disk space (`df` would confirm but can't run it — note for V)
