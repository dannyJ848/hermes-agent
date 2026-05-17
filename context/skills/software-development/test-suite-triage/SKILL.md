---
name: test-suite-triage
description: |
  Systematically triage and fix large test suites with mixed genuine failures,
  environment mismatches, and test pollution. Distinguish real regressions from
  artifacts, then fix them with minimal, targeted patches.
version: 1.0.0
created: 2026-04-27
author: Hermes Agent
metadata:
  hermes:
    tags: [testing, debugging, pytest, test-pollution, triage]
    related_skills: [systematic-debugging, test-driven-development, iteration-pipeline-wiring]
---

# Test Suite Triage

## When to Use

- `pytest` shows 20+ failures on a previously green suite
- Failures pass in isolation but fail in the full suite (test pollution)
- Environment-specific failures (macOS vs Linux, missing binaries, different Python versions)
- Tests fail after a code change that updated behavior but not expectations
- CI fails locally but passes remotely (or vice versa)

## Core Principle

**Never fix blindly. Classify first.**

Every failure falls into one of four buckets:
1. **Genuine regression** — code broke, test is correct
2. **Environment mismatch** — test assumes Linux/systemd/Python 3.10+, running on macOS/3.8
3. **Stale expectation** — code behavior changed legitimately, test wasn't updated
4. **Test pollution** — test passes alone, fails when run with others (shared state leakage)

## Phase 1: Quick Classification

Run the full suite and capture the failure list:

```bash
cd ~/project && source venv/bin/activate
pytest tests/ -n auto -q --ignore=tests/integration --ignore=tests/e2e 2>&1 | grep "^FAILED" | sort
```

For each unique test file, check isolation:

```bash
# Does it pass alone?
pytest tests/module/test_file.py -n1 -q
```

**Decision tree:**
- Passes alone + fails in full suite → **Test pollution** (defer or fix isolation)
- Fails alone + error is `ImportError`, `ModuleNotFoundError`, `SyntaxError` → **Environment mismatch**
- Fails alone + assertion mismatch on a value that changed recently → **Stale expectation**
- Fails alone + stack trace shows a real bug in the code under test → **Genuine regression**

## Phase 2: Fix Genuine Regressions First

These are the only failures that block shipping. Use `systematic-debugging` skill for each.

### Common Patterns

**Pattern A: Recent code change broke a test**
- `git log --oneline -10` to find recent commits
- `git diff HEAD~5 -- tests/failing_file.py` to see what changed
- Fix the code (not the test) unless the change was intentional

**Pattern B: Missing dependency in test environment**
- `pip install tiktoken` — token counting now needs it
- `npm ci` in a subdirectory — tests expect node_modules
- Check `pyproject.toml` or `requirements.txt` for missing entries

**Pattern C: Config/env drift**
- Test expects `HERMES_API_TIMEOUT=60` but env has `30`
- Test expects `approvals.mode: blocking` but config has `false`
- Fix: mock the config read or set the env var in the test

## Phase 3: Fix Environment Mismatches

These are tests that assume a specific platform. Fix by mocking or skipping.

### Platform-Specific Code

**systemd on macOS:**
```python
# In test:
monkeypatch.setattr(gateway_cli, "_preflight_user_systemd", lambda **kwargs: None)
```

**Linux-specific paths:**
```python
# In test:
monkeypatch.setattr(os.path, "exists", lambda p: p == expected_path)
```

**Python version syntax:**
```python
# Skip if Python < 3.10
import sys
@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+")
def test_match_case_syntax():
    ...
```

### Missing Binaries

Tests that check for `ffmpeg`, `tesseract`, etc. should mock the `shutil.which` check:

```python
@patch("tools.transcription._has_local_command", return_value=False)
def test_transcription_provider_fallback(self, mock_has_local):
    ...
```

## Phase 4: Fix Stale Expectations

When code behavior changed legitimately but tests weren't updated.

### Common Cases

**Command changed:** `npm install` → `npm ci`
```python
# Old assertion:
assert calls[0] == ["npm", "install"]
# New assertion:
assert calls[0] == ["npm", "ci"]
```

**Threshold changed:** Hardcoded token threshold restored to correct formula
```python
# Old test used 100000 (broken hardcoded value)
# New threshold is 160000 (correct formula)
# Update test input to exceed new threshold:
compressor.compress(messages, current_tokens=170000)
```

**New required fields in return value:**
```python
# Old assertion:
assert result == {"status": "ok"}
# New assertion:
assert result["status"] == "ok"
assert "new_field" in result
```

### Detection

Stale expectations often show as:
- `AssertionError: 'install' != 'ci'`
- `AssertionError: 100000 != 160000`
- `KeyError: 'new_field'` in test assertions
- `assert mock.called` is False when it should be True

## Phase 5: Handle Test Pollution

Tests that pass alone but fail in the full suite. These are the hardest to fix.

### Quick Checks

**Does order matter?**
```bash
# Run just the failing tests together
pytest tests/a.py tests/b.py tests/c.py -n1 -q
```

**Find the polluter:**
```bash
# Run each file before the failing test
for f in tests/**/*.py; do
  pytest "$f" tests/failing.py::test_name -n1 -q
  if grep -q "FAILED" output; then echo "POLLUTER: $f"; fi
done
```

### Common Pollution Sources

| Source | Symptom | Fix |
|--------|---------|-----|
| **Module-level caches** | `dict` or `list` defined at module level, mutated by tests | Reset in `setUp` or use `pytest.fixture(autouse=True)` |
| **Singleton state** | Class with `@staticmethod` or module-level instance | Add `reset()` method, call from test teardown |
| **Env var leakage** | `os.environ["X"] = "y"` in one test | Use `monkeypatch.setenv` (auto-restores) |
| **File system temp** | Tests write to `/tmp/same_file` | Use `tmp_path` fixture or `tempfile.mkdtemp()` |
| **Thread leakage** | Background threads from prior tests | Join threads in teardown or use `threading.enumerate()` guard |
| **YOLO/session state** | `_session_yolo`, `_session_approved` not cleared | Add to `_clear_approval_state()` or test teardown |

### The YOLO State Leakage Pattern

A specific case seen in approval tests:

```python
# In approval module:
_session_yolo = set()  # Module-level mutable state

# In test teardown:
def _clear_approval_state():
    _gateway_queues.clear()
    _session_approved.clear()
    _permanent_approved.clear()
    _pending.clear()
    # MISSING: _session_yolo.clear()  ← causes pollution
```

**Fix:** Add the missing clear:
```python
def _clear_approval_state():
    _gateway_queues.clear()
    _session_approved.clear()
    _permanent_approved.clear()
    _pending.clear()
    _session_yolo.clear()  # ← added
```

## Phase 6: Incremental Verification

After each fix, run the full suite to measure progress:

```bash
pytest tests/ -n auto -q --ignore=tests/integration --ignore=tests/e2e 2>&1 | tail -5
```

**Commit after each fix group:**
```bash
git add -A && git commit -m "Fix X tests: reason"
```

**Track progress:**
| Round | Total Failures | Genuine | Environment | Stale | Pollution |
|-------|---------------|---------|-------------|-------|-----------|
| 1 | 49 | 12 | 8 | 15 | 14 |
| 2 | 31 | 5 | 3 | 12 | 11 |
| 3 | 27 | 2 | 1 | 8 | 16 |
| 4 | 20 | 0 | 0 | 4 | 16 |

When genuine + environment + stale reach zero, the remaining are all pollution.

## Decision: When to Stop

**Stop when:**
- All genuine regressions are fixed
- All environment mismatches are mocked or skipped
- All stale expectations are updated
- Remaining failures are confirmed test pollution (pass in isolation)

**Do NOT chase test pollution indefinitely.** It requires a dedicated cleanup pass with proper fixtures and isolation. Document the known polluters and move on.

## Verification Checklist

- [ ] Full suite run captured all failures
- [ ] Each failure classified (genuine/environment/stale/pollution)
- [ ] All genuine regressions fixed and verified
- [ ] All environment tests mocked or skipped appropriately
- [ ] All stale expectations updated to match current behavior
- [ ] Pollution victims confirmed passing in isolation
- [ ] Incremental commits made after each fix group
- [ ] Final full suite run shows only pollution failures

## Related Skills

- `systematic-debugging` — For investigating individual genuine regressions
- `test-driven-development` — For writing new tests after fixing bugs
- `iteration-pipeline-wiring` — Pitfall 15 covers "tests calibrated to broken hardcoded values"
