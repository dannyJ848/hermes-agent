#!/bin/bash
# session-commit.sh — Copy context files from ~/.hermes/ into repo and commit
# Run after sessions to preserve MEMORY.md, SOUL.md, USER.md, MASTER.md

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTEXT_DIR="$REPO_ROOT/docs/context"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

echo "=== Session Context Commit ==="

# Ensure docs/context/ exists
mkdir -p "$CONTEXT_DIR"

# Copy context files (never .env, auth.json, config.yaml, or DBs)
for file in MEMORY.md SOUL.md USER.md MASTER.md; do
    src="$HERMES_HOME/$file"
    dst="$CONTEXT_DIR/$file"
    if [ -f "$src" ]; then
        cp "$src" "$dst"
        echo "  ✓ $file → docs/context/$file"
    else
        echo "  ⚠ $file not found in ~/.hermes/"
    fi
done

# Git commit
cd "$REPO_ROOT"
if git diff --quiet HEAD -- docs/context/ 2>/dev/null; then
    echo "  (no changes to commit)"
else
    git add docs/context/
    git commit -m "context: Session update — $(date '+%Y-%m-%d %H:%M')

Auto-commit of persistence layer context files:
- MEMORY.md
- SOUL.md
- USER.md
- MASTER.md

Refs: session-context-$(date +%s)"
    echo "  ✓ Committed to $(git branch --show-current)"
fi

echo "=== Done ==="
