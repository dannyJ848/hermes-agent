---
name: github
version: 2.0
description: GitHub workflow skills — umbrella covering repository management, PR lifecycle, code review, issue triage, authentication, headless push, upstream sync, and codebase inspection.
trigger: When working with GitHub repositories, pull requests, code reviews, issues, git operations, or GitHub CLI workflows.
---

# GitHub Skills

## Repository Management

### Clone, Create, Fork

- `gh repo clone OWNER/REPO` — clone existing repository
- `gh repo create NAME --public --source=. --push` — create and push local repo
- `gh repo fork OWNER/REPO` — fork to your account
- `gh repo list` — list your repositories
- `gh repo view OWNER/REPO --web` — open repo in browser

### Remote Management

```bash
# Add upstream remote for fork workflow
git remote add upstream https://github.com/ORIGINAL_OWNER/ORIGINAL_REPO.git
git remote -v

# Update fork from upstream
git fetch upstream
git checkout main
git merge upstream/main
```

## PR Lifecycle

### Branch → Commit → Open → CI → Merge

1. **Branch**: `git checkout -b feature/name`
2. **Commit**: `git add . && git commit -m "feat: description"`
3. **Push**: `git push -u origin feature/name`
4. **Open PR**: `gh pr create --title "Title" --body "Description"`
5. **Check CI**: `gh pr checks`
6. **Merge**: `gh pr merge --squash` or `--rebase`

### PR Review

- `gh pr list` — list open PRs
- `gh pr view NUM` — view PR details
- `gh pr checkout NUM` — checkout PR branch locally
- `gh pr review NUM --approve` — approve PR
- `gh pr review NUM --request-changes --body "Feedback"` — request changes
- `gh pr comment NUM --body "Comment"` — add comment

## Code Review

### Review PRs with diffs and inline comments

```bash
# View diff
gh pr diff NUM

# Review with comments
gh pr review NUM --comment --body "Line 42: consider error handling"

# Approve
gh pr review NUM --approve
```

## Issue Management

### Create, Triage, Label, Assign

```bash
# Create issue
gh issue create --title "Bug: ..." --body "Description..." --label bug

# List issues
gh issue list --label bug --state open

# Close issue
gh issue close NUM --comment "Fixed in #123"

# Add label
gh issue edit NUM --add-label "priority:high"
```

## Authentication

### GitHub Auth Setup

**HTTPS with token**:
```bash
gh auth login --git-protocol https
# Enter Personal Access Token when prompted
```

**SSH key**:
```bash
gh auth login --git-protocol ssh
# Or manually: ssh-keygen -t ed25519 -C "email@example.com"
# Add public key to GitHub Settings → SSH and GPG keys
```

**Verify**: `gh auth status`

## Headless Push

### Push from Remote Machines (DGX, Servers, Containers)

When git push fails with "could not read Username" from a headless machine:

**Relay via Local Machine**:
1. Clone target repo locally: `git clone --depth 1 https://github.com/USER/REPO.git relay-push`
2. Create branch for artifacts: `git checkout -b artifacts/YYYYMMDD`
3. Copy files from remote: `scp remote:/path/to/files ./`
4. Commit and push: `git add . && git commit -m "Add artifacts" && git push origin artifacts/YYYYMMDD`
5. Open PR: `gh pr create --title "Add artifacts"`

**Alternative: SSH agent forwarding**:
```bash
# On local machine
ssh-add -l  # verify key loaded
ssh -A user@remote  # forward agent
# On remote: git push works with forwarded SSH key
```

## Upstream Sync

### Surgical Cherry-Picking from Upstream

When a fork has diverged from upstream, apply selected commits without full merge:

**Pre-flight verification**:
```bash
# Check if changes are already present
for pattern in "feature-name" "function-name"; do
    grep -q "$pattern" file.py && echo "✓ $pattern already present" || echo "✗ $pattern missing"
done
```

**Cherry-pick**:
```bash
git fetch upstream
git cherry-pick abc123  # specific commit hash
# Resolve conflicts with --theirs if fork has no custom changes
git cherry-pick --continue
```

**Skip structural refactors** that require restoring deleted directories or massive dependency chains. Document what was skipped and why.

## Codebase Inspection

### Analyze Codebases with pygount

```bash
# Install
pip install pygount

# Count lines of code
pygount --format=summary ~/project

# Output: LOC, languages, ratios per language
```

## GitHub CLI (gh) Quick Reference

| Command | Action |
|---------|--------|
| `gh auth login` | Authenticate |
| `gh repo clone` | Clone repository |
| `gh pr create` | Create pull request |
| `gh pr list` | List PRs |
| `gh pr merge` | Merge PR |
| `gh issue create` | Create issue |
| `gh issue list` | List issues |
| `gh release create` | Create release |
| `gh workflow run` | Run GitHub Actions workflow |

## Pitfalls

- **SSH vs HTTPS**: Choose one protocol and stick to it. Mixing causes auth confusion.
- **Token scopes**: Ensure PAT has `repo` scope for private repositories.
- **Fork workflow**: Always add `upstream` remote to sync original repo changes.
- **Large files**: Use Git LFS for files >100MB to avoid push rejection.
- **Merge conflicts**: Resolve locally before pushing. `git merge --abort` to cancel.
- **Headless auth**: Never store PATs in plaintext on remote machines. Use SSH agent forwarding or relay approach.
