# Hermes Apparatus Full Audit — 2026-05-18

## Repository State
- **Location**: ~/.hermes/ (hermes-agent)
- **Git commit**: 4e856e29a
- **Branch**: main
- **Origin**: synced with GitHub

## Codebase Metrics
- **Total files**: 8,033
- **Python files**: 1,857
- **Markdown files**: 4,611
- **JSON files**: 1,070
- **TypeScript files**: 287
- **Shell scripts**: 98
- **YAML configs**: 96
- **Estimated total lines**: ~200,000+

## Key Modules
| Module | Files |
|--------|-------|
| hermes_cli/ | 82 |
| tools/ | 111 |
| agent/ | 172 |
| plugins/ | 46 directories |
| skills/ | 384 SKILL.md files |

## Skills State
- **Total**: 384 skills
- **Builtin**: 91
- **Local**: 293
- **Source**: ~/.hermes/skills/

## Tools State
- **Registered**: 27 (15 enabled + 12 disabled)
- **Aliases**: 76 in toolsets.py
- **Implemented**: 31 actual tool functions
- **Unimplemented**: 60 aliases without functions

## Plugins State
- **Total directories**: 46
- **Evey plugins**: 29 (evey-*)
- **Core plugins**: 17

## Cognitive Systems State
- **Files present**: 7/7 ✓
- **Orchestrator**: cognitive_orchestrator.py (972 lines)
- **Wiring status**: NOT WIRED ✗
  - No imports in CLI (main.py)
  - No plugin registration
  - No initialization calls
  - Subconscious loader: DEPRECATED

## Synchronization
- **MacBook**: commit 4e856e29a, 384 skills, 27 tools
- **DGX**: commit 4e856e29a, 384 skills, synced ✓

## Recommendations
1. Wire cognitive systems via orchestrator init
2. Implement 60 missing tool aliases
3. Add API keys to enable 12 disabled tools
4. Consider lazy-loading for 384 skills
5. Audit 172 agent/ modules for dead code
