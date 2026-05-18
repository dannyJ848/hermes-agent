---
name: skill-graduation
description: Auto-promote successful patterns to skills. When a workflow succeeds 3+ times, extract it as a reusable skill. Based on the skill graduation pattern from agent architecture research.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3]
---

# Skill Graduation Pattern

Automatically promote successful workflows to reusable skills. When a pattern works 3+ times, extract it.

## Trigger Conditions

A workflow graduates to a skill when:
1. **Used 3+ times successfully** — Same sequence, different inputs, same good outcome
2. **Solves a recurring problem** — Not a one-off fix
3. **Has clear steps** — Can be documented as numbered instructions
4. **Has known pitfalls** — You've learned what not to do

## Graduation Process

### Step 1: Identify the Pattern

After completing a task, ask:
- Did I use a specific sequence of tools?
- Did I follow a particular decision tree?
- Did I hit the same pitfalls and recover the same way?
- Would this work again with different data?

### Step 2: Extract the Skill

```yaml
# Template for new skill
name: {{descriptive_name}}
description: {{one_line_what_it_does}}
version: 1.0.0
author: Hermes Agent
---

# {{Skill Title}}

## When to Use
{{trigger_conditions}}

## Steps
1. {{step_1}}
2. {{step_2}}
3. {{step_3}}

## Pitfalls
- {{what_goes_wrong_and_how_to_fix}}

## Example
{{minimal_working_example}}
```

### Step 3: Create the Skill File

```bash
# Use skill_manage to create
skill_manage(
    action="create",
    name="{{skill_name}}",
    category="{{category}}",
    content="{{skill_content}}"
)
```

### Step 4: Test the Skill

1. Load it: `skill_view(name="{{skill_name}}")`
2. Follow the steps on a new task
3. Verify it produces the same quality result
4. Fix any gaps

### Step 5: Update After Use

Each time you use a skill:
- Note what worked
- Note what was missing
- Patch the skill immediately

```python
skill_manage(
    action="patch",
    name="{{skill_name}}",
    old_string="{{outdated_part}}",
    new_string="{{improved_part}}"
)
```

## Examples of Graduated Skills

| Pattern | Trigger Count | Skill Name |
|---------|--------------|------------|
| X cookie auth workflow | 5+ times | `x-cookie-api` |
| Claude Code PR review | 3+ times | `code-review` |
| Z.AI connection debugging | 4+ times | `zai-connection-diagnostic` |
| Subconscious integration | 10+ times | `hermes-source-surgical-integration` |

## User Preference: Class-Level Skills with Rich References

When updating the skill library, prefer CLASS-LEVEL umbrella skills over narrow one-session entries. Each skill should have:

1. **Rich SKILL.md** — comprehensive trigger conditions, steps, pitfalls, examples
2. **`references/` directory** — session-specific detail, error transcripts, reproduction recipes, research findings
3. **`templates/` directory** — starter files, boilerplate configs, known-good examples
4. **`scripts/` directory** — verification scripts, fixture generators, deterministic probes

### Update Priority (when a signal fires)

1. **UPDATE A CURRENTLY-LOADED SKILL** — If the skill was loaded this session and covers the territory, patch it first
2. **UPDATE AN EXISTING UMBRELLA** — If no loaded skill fits but an existing class-level skill does, broaden it
3. **ADD A SUPPORT FILE** under an existing umbrella — Use `references/`, `templates/`, or `scripts/` directories
4. **CREATE A NEW CLASS-LEVEL UMBRELLA** — Only when no existing skill covers the class

### Signals That Warrant Action

- User corrected style, tone, format, legibility, or verbosity
- User corrected workflow, approach, or sequence of steps
- Non-trivial technique, fix, workaround, or debugging path emerged
- A loaded skill was wrong, missing a step, or outdated

### Naming Rules

- MUST be class-level (e.g., `dgx-spark-qwen3-deployment`, not `fix-vllm-0.20.2-fp8`)
- MUST NOT be a specific PR number, error string, feature codename, or session artifact
- If the name only makes sense for today's task, it's wrong — use an umbrella instead

### Anti-Patterns

- ❌ Creating narrow skills for single sessions
- ❌ Dumping raw session logs without structure
- ❌ Flat list of 100+ micro-skills instead of 10-20 rich umbrellas
- ❌ Putting procedural knowledge in memory instead of skills

## Automated Skill Graduation from Tips

The self-evolution pipeline in `agent/self_evolution.py` now auto-graduates high-performing tips to skills:

### Criteria for Auto-Graduation
- **Elo >= 1800** — tip has won enough Elo tournaments
- **survival_count >= 5** — tip has been applied successfully 5+ times
- **application_count >= 3** — tip has been used in 3+ different contexts
- **No existing skill** — skill name derived from tip text doesn't already exist

### How It Works

```python
# In SelfEvolutionPipeline.run_cycle():
def run_cycle(self):
    # Step 1-3: distill, tournament, evolve
    distilled = self.distill_from_experiences(limit=50)
    tournament = self.run_elo_tournament(num_matches=20)
    evolved = self.evolve_tips(num_mutations=5)
    
    # Step 4: Auto-graduate top tips to skills
    graduated = self._graduate_tips_to_skills()
    # Returns: number of tips promoted to ~/.hermes/skills/
```

### Skill Naming

Derived from tip content automatically:
```python
words = re.sub(r'[^\w\s]', '', tip_text).lower().split()[:5]
skill_name = "-".join(words)  # e.g. "think-before-acting-state-assumptions"
```

### Skill File Format

```markdown
---
name: think-before-acting-state-assumptions
category: general
source: auto-graduated (tip abc123)
elo: 1850
survival: 7
applications: 4
created: 2026-07-10T14:30:00
---

# think-before-acting-state-assumptions

{tip_text}

## When to Use

This skill was automatically graduated from a high-performing tip...
```

### Manual vs Auto

| Aspect | Manual Graduation | Auto-Graduation |
|--------|------------------|-----------------|
| Trigger | After 3+ successful uses | Elo >= 1800 + survival >= 5 |
| Quality | Human-curated | Tournament-proven |
| Speed | After each session | Every evolution cycle |
| Naming | Descriptive | Content-derived |

Both coexist — auto-graduation handles high-volume tip flow; manual graduation captures nuanced patterns the Elo system misses.

## Hermes Integration

The `skill_manage` tool handles creation, patching, and deletion. Use it proactively:

```python
# After any complex task (5+ tool calls)
if task_succeeded and pattern_reusable:
    skill_manage(action="create", ...)

# After using a skill and finding a gap
skill_manage(action="patch", name="skill_name", old_string="...", new_string="...")
```

## Current Skills Inventory

Check existing skills before creating new ones:
```bash
skills_list()  # See all available skills
```

Categories:
- `software-development` — Coding, debugging, architecture
- `devops` — Deployment, infrastructure, monitoring
- `meta` — Agent behavior, self-improvement, workflows
- `research` — Information gathering, analysis
- `creative` — Content generation, design
