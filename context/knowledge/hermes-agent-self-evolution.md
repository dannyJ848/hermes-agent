# hermes-agent-self-evolution

*Researched: 2026-04-01 22:24 CDT*

# Hermes Agent Self-Evolution — DSPy + GEPA Optimization

**Source:** [NousResearch/hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution) (★340, MIT License)

## Overview
Official self-improvement pipeline for Hermes Agent. Uses DSPy + GEPA (Genetic-Pareto Prompt Evolution) to evolve skills, tool descriptions, system prompts, and code — no GPU required. ~$2-10 per optimization run.

## Core Pipeline
```
Read current skill/prompt/tool → Generate eval dataset
                                      ↓
                                GEPA Optimizer ← Execution traces
                                      ↓                  ↑
                                Candidate variants → Evaluate
                                      ↓
                                Constraint gates (tests, size, benchmarks)
                                      ↓
                                Best variant → PR against hermes-agent
```

## Key Components

### SkillModule (`skill_module.py`)
- Wraps SKILL.md as a DSPy module where the skill text is the optimizable parameter
- `load_skill()`: Parses YAML frontmatter + markdown body from SKILL.md
- `find_skill()`: Searches skills directory by name (direct + fuzzy match)
- `SkillModule(dspy.Module)`: Uses `dspy.ChainOfThought(TaskWithSkill)` signature
- `reassemble_skill()`: Rebuilds SKILL.md preserving frontmatter, replacing body

### Fitness Scoring (`fitness.py`)
- Multi-dimensional LLM-as-judge evaluation:
  - **Correctness** (50% weight): Did the agent produce correct output?
  - **Procedure Following** (30%): Did it follow the skill's procedure?
  - **Conciseness** (20%): Was it appropriately concise?
- **Length penalty**: Ramps from 0 at 90% size limit to 0.3 at 100%+
- Judge uses `dspy.ChainOfThought(JudgeSignature)` with rubric-based scoring
- Returns textual feedback that GEPA uses for reflective mutation

### Constraint Validation (`constraints.py`)
- Size limits: Skills ≤15KB, tool descriptions ≤500 chars, params ≤200 chars
- Growth limit: Max 20% growth over baseline (prevents bloat)
- Non-empty validation
- Structural integrity: Must have YAML frontmatter with name + description
- Test suite: Full `pytest` must pass 100% (5-minute timeout)
- All constraints must pass — any failure = immediate rejection

### Dataset Building (`dataset_builder.py`)
Three sources:
1. **Synthetic**: LLM reads skill/tool and generates test cases (task_input, expected_behavior, difficulty, category)
2. **SessionDB**: Mine real usage from Claude Code, Copilot, Hermes session history
3. **Golden**: Hand-curated JSONL files
- Splits into train/val/holdout (50/25/25)
- Each example: task_input + expected_behavior rubric

### External Importers (`external_importers.py`)
- Bridges existing tool usage into eval datasets
- Sources: Claude Code (`~/.claude/history.jsonl`), GitHub Copilot (`~/.copilot/`), Hermes (`~/.hermes/sessions/`)
- **Secret detection**: Regex patterns for API keys, tokens, passwords — never included in datasets
- **Skill relevance filter**: Keyword overlap + LLM scoring to find relevant examples
- Solves cold-start problem: new users have session history from other tools

## Evolution Phases
| Phase | Target | Status |
|-------|--------|--------|
| Phase 1 | Skill files (SKILL.md) | ✅ Implemented |
| Phase 2 | Tool descriptions | 🔲 Planned |
| Phase 3 | System prompt sections | 🔲 Planned |
| Phase 4 | Tool implementation code | 🔲 Planned |
| Phase 5 | Continuous improvement loop | 🔲 Planned |

## SOMA Application
1. **Skill Optimization**: Run GEPA on medical skills (anatomy-3d-viewer, ts-error-batch-fix) to improve success rates
2. **Tool Description Tuning**: Optimize which tools the agent selects for medical tasks
3. **Eval Dataset Mining**: Use our session history to build medical-specific evaluation sets
4. **Constraint Customization**: Add medical accuracy constraints (hallucination detection)
5. **Continuous Loop**: Set up overnight evolution similar to Dojo's `/dojo auto` pattern


## Sources

- https://github.com/NousResearch/hermes-agent-self-evolution
