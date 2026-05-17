---
name: project-cleanup
description: Clean up project directories cluttered by AI agent dump files, one-shot scripts, and status reports. Reorganize for a clean development foundation.
version: 1.0
---

# Project Cleanup - Recovering from AI Agent Mess

Clean up a project directory that has been cluttered by automated tools or AI agents dumping status reports, one-shot scripts, and temporary files into the root directory.

## When to Use
- Project root has hundreds of non-essential files (agent reports, one-shot scripts, status files)
- Need to reorganize before meaningful development can continue
- Large codebase where `git add -A` may timeout

## Steps

### 1. Audit and Categorize
```python
# Categorize every file in root into: keep / archive_reports / archive_scripts / delete
# Use filename prefixes and extensions to bucket files:
#   AGENT_*, BETA_*, DELTA_*, GAMMA_*, EPSILON_* -> agent reports
#   *.py one-shot scripts -> archive
#   *.sh fix scripts -> archive
#   Stray *.ts in root that aren't vite config -> archive
#   Status/summary markdown -> archive
```

Print the full categorization plan for review before moving anything.

### 2. Create Archive Structure
```bash
mkdir -p _archive/reports _archive/scripts _archive/misc
```

### 3. Move Files in Batches by Category
Move in phases (agent reports -> scripts -> misc) using `mv` with explicit file lists. Use `2>/dev/null` to silently skip files that don't exist.

### 4. Handle Large Repo Git Init
For repos with 100MB+ of source data:
- `git add -A` will likely timeout on large codebases (especially with 4000+ source files)
- **Add in stages**: config files first, then small dirs, then large dirs one at a time
- If git lock file gets stuck: `pkill -f git; sleep 2; rm -f .git/index.lock`
- May need multiple attempts

```bash
# Staged approach to avoid timeout
git add .gitignore package.json tsconfig.json vite.config.ts
git add src/
git add small_dirs/
git add large_core_dir/  # this one may need timeout=300
```

### 5. Update .gitignore
Add entries for:
```
_archive/
venv/
__pycache__/
*.pyc
chroma_db/
*.tsbuildinfo
```

### 6. Verify
- Count files in root before/after
- Try a build to confirm nothing essential was moved
- Check `git status` shows clean state

## Pitfalls
- **Don't delete, only archive** -- files may be needed later for reference
- **Don't move files referenced by package.json** (vite.config.ts, tsconfig.json, etc.)
- **Git lockfile hell** -- on large repos, git operations can crash and leave `.git/index.lock`. Always check for and remove it before retrying.
- **Spaces in paths** -- if the project path has spaces, always quote paths in shell commands
- **Check what's imported** -- before moving .ts files from root, grep to see if anything imports them
