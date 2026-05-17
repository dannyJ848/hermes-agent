# Autobrowse Strategy Scratchpad

This document captures what the agent learns from its own execution traces.
Read this before starting new tasks to compound improvements.

## [2026-05-07 22:00] Session: autobrowse_init

**Task**: Initialize Autobrowse self-improvement system

### Observations

- **system_init** (severity=0.00): Autobrowse modules built and tested successfully
  - *Fix*: No action needed — system operational

### What Worked

- Building 4 modules (tracer, analyzer, synthesizer, graduator) in one session
- Self-test pattern with MockTrace/MockPattern objects
- Line-index based patching for multi-line string fixes

### What to Try Next

- [ ] Wire modules into distillation plugin
- [ ] Test trace capture on real tool calls
- [ ] Run first analysis cycle after 20 tool calls
- [ ] Verify tip generation feeds into CortexDB


## [2026-05-07 22:31] Session: test_pipeline

**Task**: Testing full autobrowse pipeline

### Observations

- **redundant_loop** (severity=0.60): web_search called 3x with similar input: '{'query': 'python tutorial'}...'
  - *Fix*: WHEN calling web_search repeatedly, DO cache results or batch requests

- **redundant_loop** (severity=1.00): read_file called 19x with similar input: '{'path': '/tmp/test.txt'}...'
  - *Fix*: WHEN calling read_file repeatedly, DO cache results or batch requests

- **suboptimal_model** (severity=0.60): Expensive model 'claude-opus' used for simple tool web_search
  - *Fix*: WHEN using web_search, DO use glm-5.1 or gemini-flash instead of claude-opus

- **token_waste** (severity=0.88): web_search returned 3500 tokens for 30 input tokens
  - *Fix*: WHEN searching, DO limit max_chars or use targeted queries to reduce token waste

- **failure_cluster** (severity=0.50): TimeoutError occurred 2 times in recent traces
  - *Fix*: WHEN seeing TimeoutError, DO check preconditions before calling the tool

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN calling web_search repeatedly, DO cache results or batch requests
- [ ] Address redundant_loop: WHEN calling read_file repeatedly, DO cache results or batch requests
- [ ] Address suboptimal_model: WHEN using web_search, DO use glm-5.1 or gemini-flash instead of claude-opus
- [ ] Address token_waste: WHEN searching, DO limit max_chars or use targeted queries to reduce token waste

## [2026-05-07 22:31] Session: test_injections

**Task**: Debug failing deployment

### Observations

- **failure_cluster** (severity=1.00): ConnectionError occurred 8 times in recent traces
  - *Fix*: WHEN seeing ConnectionError, DO check preconditions before calling the tool

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address failure_cluster: WHEN seeing ConnectionError, DO check preconditions before calling the tool

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 0 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 0
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 1 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 1
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 2 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 2
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 3 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 3
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 4 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 4
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 5 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 5
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 6 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 6
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 7 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 7
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 8 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 8
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 9 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 9
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 10 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 10
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 11 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 11
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 12 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 12
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 13 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 13
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:32] Session: test_persistence

**Task**: Session 14 task

### Observations

- **redundant_loop** (severity=0.70): web_search called 3x in session 14
  - *Fix*: WHEN searching repeatedly, DO cache results

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN searching repeatedly, DO cache results

## [2026-05-07 22:30] Session: autobrowse_r191_build

**Task**: Build and test Autobrowse self-improvement system (R191)

### What Worked

- Building 4 modules (tracer, analyzer, synthesizer, graduator) in one session
- Self-test pattern with MockTrace/MockPattern objects
- Line-index based patching for multi-line string fixes
- Direct execute_code wiring instead of fragile sed/terminal
- All 6 tests passed: pipeline, injection, persistence, thresholds, wiring, edge cases

### Key Decisions

- R191 wired into distillation plugin (not standalone plugin)
- post_tool_call: trace capture + analysis every 20 calls
- pre_llm_call: 4 injection sources (tracer stats, analyzer patterns, strategy.md, graduator status)
- Strategy.md auto-prunes at 2000 lines to prevent bloat
- Tips use WHEN/DO format for direct injectability

### What to Try Next

- [ ] Monitor first real trace captures in production
- [ ] Verify analysis triggers after 20 actual tool calls
- [ ] Check strategy.md grows with real session data
- [ ] Test graduator promotions when tips reach thresholds
- [ ] Consider adding model cost data to trace metadata


## [2026-05-08 23:12] Session: test_live

**Task**: batch_20

### Observations

- **redundant_loop** (severity=1.00): terminal called 14x with similar input: '{'query': 'test'}...'
  - *Fix*: WHEN calling terminal repeatedly, DO cache results or batch requests

- **redundant_loop** (severity=1.00): web_search called 6x with similar input: '{'query': 'test'}...'
  - *Fix*: WHEN calling web_search repeatedly, DO cache results or batch requests

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN calling terminal repeatedly, DO cache results or batch requests
- [ ] Address redundant_loop: WHEN calling web_search repeatedly, DO cache results or batch requests

## [2026-05-08 23:31] Session: default

**Task**: test_batch

### Observations

- **redundant_loop** (severity=1.00): terminal called 13x with similar input: '{'query': 'test'}...'
  - *Fix*: WHEN calling terminal repeatedly, DO cache results or batch requests

- **redundant_loop** (severity=1.00): web_search called 7x with similar input: '{'query': 'test'}...'
  - *Fix*: WHEN calling web_search repeatedly, DO cache results or batch requests

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN calling terminal repeatedly, DO cache results or batch requests
- [ ] Address redundant_loop: WHEN calling web_search repeatedly, DO cache results or batch requests

## [2026-05-09 00:41] Session: default

**Task**: test context

### Observations

- **failure_cluster** (severity=1.00): TimeoutError occurred 4 times in recent traces
  - *Fix*: WHEN seeing TimeoutError, DO check preconditions before calling the tool

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address failure_cluster: WHEN seeing TimeoutError, DO check preconditions before calling the tool

## [2026-05-09 10:27] Session: default

**Task**: live_test_session

### Observations

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool web_search
  - *Fix*: WHEN using web_search, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool web_extract
  - *Fix*: WHEN using web_extract, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool read_file
  - *Fix*: WHEN using read_file, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool search_files
  - *Fix*: WHEN using search_files, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool web_search
  - *Fix*: WHEN using web_search, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool web_extract
  - *Fix*: WHEN using web_extract, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool read_file
  - *Fix*: WHEN using read_file, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool search_files
  - *Fix*: WHEN using search_files, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool web_search
  - *Fix*: WHEN using web_search, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool web_extract
  - *Fix*: WHEN using web_extract, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool read_file
  - *Fix*: WHEN using read_file, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool search_files
  - *Fix*: WHEN using search_files, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool web_search
  - *Fix*: WHEN using web_search, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

- **failure_cluster** (severity=1.00): TimeoutError occurred 4 times in recent traces
  - *Fix*: WHEN seeing TimeoutError, DO check preconditions before calling the tool

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address suboptimal_model: WHEN using web_search, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using web_extract, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using read_file, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using search_files, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using web_search, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using web_extract, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using read_file, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using search_files, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using web_search, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using web_extract, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using read_file, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using search_files, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address suboptimal_model: WHEN using web_search, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
- [ ] Address failure_cluster: WHEN seeing TimeoutError, DO check preconditions before calling the tool

## [2026-05-09 11:42] Session: default

**Task**: smoke test task

### Observations

- **redundant_loop** (severity=0.60): web_search called 3x with similar input: '{'query': 'same query'}...'
  - *Fix*: WHEN calling web_search repeatedly, DO cache results or batch requests

- **suboptimal_model** (severity=0.60): Expensive model 'deepseek-v4-pro' used for simple tool read_file
  - *Fix*: WHEN using read_file, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro

### What Worked

- No major issues detected in this batch

### What to Try Next

- [ ] Address redundant_loop: WHEN calling web_search repeatedly, DO cache results or batch requests
- [ ] Address suboptimal_model: WHEN using read_file, DO use glm-5.1 or gemini-flash instead of deepseek-v4-pro
