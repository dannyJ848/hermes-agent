---
name: third-party-repo-security-audit
description: >
  Systematic security audit of third-party GitHub repos before installing as Hermes plugins,
  dependencies, or tools. Reviews every source file for malicious patterns. Covers Python,
  Shell, config, and binary trust assessment.
version: "1.0"
author: evey
tags: [security, audit, github, plugin]
---

# Third-Party Repo Security Audit

Use before installing ANY third-party code (Hermes plugins, npm packages, CLI tools, shell scripts).
Especially critical for agent plugins that run with full system access.

## Audit Checklist

### 1. Repo Metadata (red flags)
- [ ] Author reputation (GitHub profile, stars, forks, commit history)
- [ ] Is it endorsed/linked by the platform it targets (e.g. NousResearch for Hermes)?
- [ ] License present? (MIT/Apache = good, no license = caution)
- [ ] Recent creation date with many commits = possible rush job
- [ ] Single contributor = higher trust risk than org-backed

### 2. File Inventory
Get the FULL file list first:
```
Browser → github.com/OWNER/REPO → find/master (file finder)
```
Or use the GitHub API tree endpoint.

Note: binaries (bin/), models, .so/.dylib files = cannot be audited by reading.

### 3. Source Code Review (read EVERY file)
For each `.py`, `.sh`, `.js`, `.ts` file:

**CRITICAL PATTERNS TO FLAG:**
- `eval()`, `exec()`, `compile()` — code execution from strings
- `os.system()`, `subprocess.call()` with unsanitized input
- Network calls to unexpected hosts (not github.com, pypi.org)
- Reading env vars for secrets: `os.environ.get("API_KEY"...)`
- File access outside declared paths (`/etc/passwd`, `~/.ssh/`, `~/.aws/`)
- Obfuscated strings: base64 decode, hex encoding, rot13
- Downloading and executing: `curl ... | bash`, `wget ... | sh`
- Modifying other apps' configs without clear purpose
- Daemon/background process spawning

**ACCEPTABLE PATTERNS:**
- `subprocess.run(["toolname", ...])` with fixed args
- Reading declared config files only
- Standard HTTP to known APIs
- Clean argument parsing

### 4. Install Scripts (highest risk)
Read install.sh / setup.py / postinstall hooks completely.

Check for:
- [ ] What gets downloaded and from where (URLs)
- [ ] Where files are placed (should be ~/.local or declared paths)
- [ ] Telemetry/phone-home calls (curl POST to external servers)
- [ ] `rm -rf` commands — what do they delete?
- [ ] Modifications to other applications' config files
- [ ] PATH modifications or shell profile changes

### 5. Binary Trust Assessment
Pre-compiled binaries CANNOT be audited by reading source.

Options:
1. **Trust it** — if author is reputable and many users (stars/forks)
2. **Compile from source** — look for source repo, build yourself
3. **Skip** — if not worth the trust risk

Check: does the source repo exist? Can you build from it instead?

### 6. Telemetry Detection
Search for:
- `curl -X POST` or `requests.post` to external URLs
- Google Analytics, Mixpanel, Segment, etc.
- Any analytics/telemetry in function names
- Background process spawns (`&` at end of commands)

### 7. Report Template
```
## [REPO] Security Audit

**Files reviewed:** [list all]
**Green flags:** [what looked good]
**Yellow flags:** [minor concerns]
**Red flags:** [dealbreakers]
**Binary trust:** [assessment]
**Verdict:** [install / skip / compile from source]
```

## Tools
- `web_extract(url=raw.githubusercontent.com/...)` — read individual files
- `browser_navigate` + `browser_snapshot` — browse repo structure
- GitHub file finder (`/find/master`) — complete file inventory

## Lessons Learned
- install.sh scripts commonly have telemetry pings — check for `curl -X POST` at the end
- Hermes plugins run with full system access — treat them like root-level software
- The PII scrubber may prevent patching sensitive values — use Python file I/O directly
- Always check if the source repo exists for pre-compiled binaries
- **SOURCE VERIFICATION GAP (Apr 2026):** A repo can reference a source repo (e.g. CLAUDE.md says "source at enzyme-rust") that DOESN'T EXIST (404). Always verify referenced source repos with `verify_repo` or direct URL check. Plugin wrapper code being clean means nothing if the compiled binary is unauditable.
- **GitHub API tree listing** (`api.github.com/repos/OWNER/REPO/git/trees/main?recursive=1`) gives the complete file inventory in one call — faster than browsing.
- **Check `language` field** in repo metadata. If a binary tool repo shows language as "Shell" with no Rust/Go/C source, the core is closed-source regardless of claims.
- When auditing a Hermes plugin: the Python wrapper is LOW risk (just subprocess calls). The binary it downloads is HIGH risk. Separate the trust assessment.
