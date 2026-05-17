# uworld-project-full-reflection-apr2026

*Researched: 2026-04-14 15:14 CDT*

# Full USMLE Study Automation Project Retrospective (AnKing + UWorld)

## Project: 5,899 Precision-Targeted Study Cards for USMLE Step 1

### Phase 1: AnKing Filtered Deck (4,077 cards)
- Analyzed 295 missed questions from 5 practice exams (NBME 28-30, UWSA 2-3)
- Identified 38 precision subtopics across 5 weak systems (Neuro, Cardio, Resp, Heme/Immuno, Endo)
- Generated 3,449-char AnKing tag search string
- Bypassed AnkiConnect API limits with custom add-on (hermes_patch_limit)
- Result: 4,077 cards

### Phase 2: UWorld QBank Extraction (1,822 cards)
- Reverse-engineered UWorld REST API via Chrome CDP
- 4 endpoints, 4 custom auth headers, PascalCase payload format
- Split into Phase 1 (scan 186 tests) and Phase 2 (create cards)
- 3 critical silent bugs found and fixed: type mismatch, batch dup drop, filter coverage
- Result: 1,822 cloze cards with AnKing-matching CSS + mobile optimization

## Top 10 Lessons (distilled into Cortex as tips)
1. Silent failures are most dangerous — verify counts independently
2. Type-check ALL API fields before comparison
3. AnkiConnect batch needs individual fallback for duplicates
4. Verify filter coverage with count scan before committing
5. Capture EXACT request body from browser, use verbatim
6. Local Chrome CDP over remote browsers for auth-heavy sites
7. Pre-project system hardening saves hours of freeze recovery
8. 3-pass pipeline: scope → build rough → refine format
9. Save decision RATIONALE in checkpoints, not just outcomes
10. Copy ALL custom headers from first successful request

## System Improvements Triggered
- TCP keepalive patches (2hr → 60s dead socket detection)
- Docker memory reduction (8GB → 4GB, freed 32GB disk)
- Ghost injection bug fix (context_health_guard file-size heuristic)
- LCM context engine installation (DAG-based, not flat summarization)
- macOS TCP keepidle persistence via LaunchDaemon


## Sources

- session:20260413_215447_795a06
- session:20260414_113106_74aada
- session:20260414_130307_36efe4
- session:20260414_134505_6cd910
