---
name: third-party-security-audit
description: >
  Security audit for any third-party code, plugin, repo, or tool before integration.
  Mandatory when the source is NOT from Nous Research. Covers source availability,
  code review, binary trust, data exfiltration, and supply chain risks.
triggers:
  - User asks to install/integrate a tool, plugin, repo, or dependency
  - Source is NOT Nous Research (github.com/NousResearch/*)
  - Any curl | bash install, pre-compiled binary, or pip/npm package from unknown authors
---

# Third-Party Security Audit

## Gate 0: Source Verification

Before ANY code review, answer:

1. **Is this from Nous Research?** (github.com/NousResearch/*) → If YES, reduced audit (still check for typosquatting)
2. **Does the author match the claimed identity?** Check GitHub profile age, activity, other repos
3. **Is the source code public and complete?** Check for missing source repos, binary-only distributions

**STOP and report** if any of these are suspicious. Do NOT install.

## Gate 1: File Inventory

Get the COMPLETE file tree of the repo. Use GitHub API:
```
https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1
```

Categorize every file:
- **Source code** (.py, .rs, .ts, .js, .go, .sh) — MUST read all
- **Binaries** (.exe, .bin, compiled binaries, .so, .dylib) — flag for trust assessment
- **Config** (.yaml, .json, .toml) — read for suspicious endpoints/permissions
- **Models** (.onnx, .gguf, .bin) — verify provenance
- **Install scripts** (install.sh, setup.py, Makefile) — CRITICAL, read in full

## Gate 2: Code Review (read EVERY source file)

For each source file, check:

### Network calls
- [ ] Any `requests.get/post`, `fetch()`, `curl`, `wget`, `http.Client`?
- [ ] Any URL that isn't the project's own GitHub/API?
- [ ] Base64-encoded URLs or obfuscated endpoints?
- [ ] DNS exfiltration patterns (encoding data in subdomain queries)?

### File system access
- [ ] Reads files outside declared scope (e.g., reads ~/.ssh, ~/.aws, browser profiles)?
- [ ] Writes to unexpected locations (system dirs, other apps' configs)?
- [ ] `rm -rf` or destructive operations? What paths?
- [ ] Modifies other tools' configs (Claude Desktop, Cursor, etc.)?

### Credential/token access
- [ ] Reads environment variables beyond what's declared?
- [ ] Accesses keychain, credential files, .env files outside its own directory?
- [ ] Sends auth tokens, cookies, or API keys anywhere?

### Code execution
- [ ] `eval()`, `exec()`, `subprocess.call()` with unsanitized input?
- [ ] Downloads and executes code at runtime?
- [ ] Shell injection vectors in user-facing inputs?

### Supply chain
- [ ] Unusual dependencies (little-known packages, typo-squatted names)?
- [ ] Pins dependency versions or uses floating latest?
- [ ] Post-install hooks that phone home?

### Telemetry/data collection
- [ ] Any analytics, telemetry, or tracking pixels?
- [ ] Sends data to external servers? What data? How frequently?
- [ ] Is it documented and opt-in, or silent?

## Gate 3: Binary Trust Assessment

If the repo includes pre-compiled binaries:

1. **Is the source code available?** Check for a separate source repo, Cargo.toml, go.mod, etc.
2. **Can you build from source?** Verify the build reproduces the same binary
3. **Binary metadata**: Check size, architecture match, code signing
4. **Hash verification**: Does the repo provide SHA256 checksums? Verify against release

**RISK LEVELS:**
- Source available + reproducible build → LOW RISK
- Source available but not verified → MEDIUM RISK  
- Source NOT available → HIGH RISK (report to user, do NOT install without explicit approval)

## Gate 4: Author & Community Assessment

- **GitHub account age and activity** — new account with few repos = suspicious
- **Stars/forks ratio** — low engagement could mean untested
- **Issue tracker** — open security issues? Responsive maintainer?
- **Commit history** — single author? Recent mass commits? Bots?
- **License** — no license = legal risk, restrictive license = usage risk
- **Known vulnerabilities** — check `https://github.com/{owner}/{repo}/security/advisories`

## Gate 5: Install Procedure Review

Read the full install script/command BEFORE executing:

1. `curl ... | bash` — read the script FIRST via `web_extract`
2. `pip install` — check the package on PyPI, inspect the tarball
3. `npm install` — check package.json for postinstall scripts
4. Manual git clone — check for git hooks in `.githooks/`

**NEVER pipe curl to bash without reading the script first.**

## Output Format

Present audit results as:

```
SECURITY AUDIT: {owner}/{repo}
Audit date: YYYY-MM-DD
Risk level: LOW / MEDIUM / HIGH / CRITICAL

FILES REVIEWED: [list all files read]

GREEN FLAGS:
- [positive findings]

YELLOW FLAGS:
- [concerns that aren't dealbreakers]

RED FLAGS:
- [dealbreakers, must-fix issues]

BINARY TRUST:
- Source available: YES/NO
- Source repo: [url or "NOT FOUND"]
- Reproducible build: YES/NO/UNKNOWN

RECOMMENDATION: INSTALL / DON'T INSTALL / INSTALL WITH CAVEATS
```

## Rules
1. NEVER skip a gate because "it looks fine"
2. NEVER install before completing the full audit
3. ALWAYS flag closed-source binaries as HIGH RISK
4. ALWAYS report telemetry/phoning-home to the user
5. If in doubt, recommend waiting for trusted third-party review
6. For Nous Research repos: run reduced audit (Gates 1-2 only, skip binary trust)
