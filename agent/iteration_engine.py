#!/usr/bin/env python3
"""
Evey's Iteration Engine — v1.0
Instantaneous experiential learning. Every action, every result, every time.

DESIGN PRINCIPLE: Trip over the shoe ONCE. Never again.

HOW IT WORKS:
  BEFORE every action:
    1. Hash the action signature (what I'm about to do)
    2. Look up: have I done something like this before?
    3. If yes: retrieve the lesson instantly (no model call, pure DB lookup)
    4. Inject the lesson into context so I don't repeat mistakes

  AFTER every action:
    1. Capture: what I tried, what happened, how long it took
    2. If it failed: extract the exact error pattern
    3. If it succeeded: record what approach worked
    4. Store as an "experience" with the action signature as the lookup key
    5. If a similar experience existed and was wrong: UPDATE it (we learned)

  SPEED: All lookups are indexed hash queries. Sub-millisecond.
  No model calls. No reflection. Just pattern matching against reality.

TABLE: experiences
  - action_hash:    hash of action type + key parameters (fast lookup)
  - action_type:    patch, terminal, write_file, delegate, etc.
  - action_detail:  what was attempted (file path, command, etc.)
  - result:         success | failure | partial
  - error_pattern:  the specific error if it failed (regex-matchable)
  - lesson:         what to do differently (1-2 sentences)
  - approach:       the approach that worked (if success)
  - iterations:     how many attempts before success
  - last_seen:      timestamp of most recent occurrence
  - frequency:      how many times this pattern has occurred
  - speed_ms:       how long the successful attempt took
"""

import hashlib
import json
import re
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


class IterationEngine:
    """
    The shoe-detector. Runs before and after every action.
    Sub-millisecond lookups. No model calls. Pure pattern memory.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._local = threading.local()
        self._session_actions = []  # Track current session for batch learning

    @property
    def conn(self):
        """Thread-local connection — each thread gets its own."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path))
            self._local.conn.row_factory = sqlite3.Row
            self._ensure_table()
        return self._local.conn

    def _ensure_table(self):
        """Create the experiences table if it doesn't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_hash TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_detail TEXT DEFAULT '',
                action_fingerprint TEXT DEFAULT '',
                result TEXT DEFAULT 'unknown',
                error_pattern TEXT DEFAULT '',
                error_snippet TEXT DEFAULT '',
                lesson TEXT DEFAULT '',
                approach TEXT DEFAULT '',
                fix_command TEXT DEFAULT '',
                iterations INTEGER DEFAULT 1,
                frequency INTEGER DEFAULT 1,
                speed_ms INTEGER DEFAULT 0,
                last_seen REAL DEFAULT 0,
                created_at REAL DEFAULT 0,
                context_tags TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_exp_hash ON experiences(action_hash);
            CREATE INDEX IF NOT EXISTS idx_exp_type ON experiences(action_type);
            CREATE INDEX IF NOT EXISTS idx_exp_error ON experiences(error_pattern);
            CREATE INDEX IF NOT EXISTS idx_exp_result ON experiences(result);
        """)
        self.conn.commit()

    # ── HASHING ──
    # The hash is the lookup key. It captures the "shape" of an action
    # so we can match similar situations without exact string matching.

    def _hash_action(self, action_type: str, detail: str, extra: str = "") -> str:
        """
        Create a stable hash for an action type + its key characteristics.
        Not exact content — the SHAPE of the action.
        """
        # Normalize: lowercase, strip specific values, keep structure
        normalized = action_type.lower().strip()

        # Extract structural patterns from detail
        if action_type in ("patch", "write_file"):
            # For code: hash the file extension + the type of change, not the content
            detail_str = str(detail)
            ext = Path(detail_str).suffix if "." in detail_str else "unknown"
            normalized += f":{ext}"
        elif action_type == "terminal":
            # For commands: hash the base command, not the arguments
            detail_str = str(detail)
            cmd = detail_str.split()[0] if detail_str.split() else "unknown"
            normalized += f":{cmd}"
        elif action_type == "delegate":
            normalized += f":{str(detail)[:50]}"
        elif action_type == "search":
            normalized += f":{str(detail)[:30]}"

        if extra:
            normalized += f":{extra[:50]}"

        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _hash_error(self, error) -> str:
        """Hash an error pattern for matching similar errors."""
        if not error:
            return ""
        error = str(error)
        # Strip specific values (file paths, line numbers, variable names)
        cleaned = re.sub(r'/[^\s]+', '<PATH>', error)
        cleaned = re.sub(r'\d+', 'N', cleaned)
        cleaned = re.sub(r"'[^']*'", '<STR>', cleaned)
        cleaned = re.sub(r'"[^"]*"', '<STR>', cleaned)
        return hashlib.sha256(cleaned.encode()).hexdigest()[:16]

    # ── BEFORE ACTION: Retrieve lessons ──

    def before_action(self, action_type: str, detail: str = "",
                      extra: str = "") -> Dict:
        """
        Call BEFORE any action. Returns relevant lessons from past experiences.
        This is the "look down at your feet before you walk" function.
        """
        action_hash = self._hash_action(action_type, detail, extra)

        # Look up exact hash matches (same action shape)
        exact_matches = self.conn.execute(
            """SELECT lesson, approach, fix_command, error_pattern, result,
                      frequency, iterations, speed_ms
               FROM experiences WHERE action_hash = ? ORDER BY last_seen DESC LIMIT 3""",
            (action_hash,)
        ).fetchall()

        # Look up recent failures of this action type
        recent_failures = self.conn.execute(
            """SELECT lesson, error_pattern, error_snippet, action_detail, frequency
               FROM experiences
               WHERE action_type = ? AND result = 'failure'
               ORDER BY last_seen DESC LIMIT 5""",
            (action_type,)
        ).fetchall()

        lessons = []
        warnings = []
        approaches = []

        for m in exact_matches:
            if m["lesson"] and m["result"] == "failure":
                warnings.append({
                    "lesson": m["lesson"],
                    "error": m["error_pattern"],
                    "frequency": m["frequency"],
                    "iterations": m["iterations"],
                })
            elif m["lesson"] and m["result"] == "success":
                approaches.append({
                    "approach": m["approach"] or m["lesson"],
                    "speed_ms": m["speed_ms"],
                    "frequency": m["frequency"],
                })

        for f in recent_failures:
            if f["lesson"] and f["lesson"] not in [w["lesson"] for w in warnings]:
                warnings.append({
                    "lesson": f["lesson"],
                    "error": f["error_pattern"],
                    "detail": f["action_detail"],
                    "frequency": f["frequency"],
                })

        # Calculate confidence score (0.0 - 1.0)
        # Based on: frequency, success ratio, and recency of observations
        total_exact = len(exact_matches)
        successes = sum(1 for m in exact_matches if m["result"] == "success")
        failures = sum(1 for m in exact_matches if m["result"] == "failure")
        total_freq = sum(m["frequency"] for m in exact_matches)

        # Frequency factor: more observations = higher confidence (capped at 1.0)
        freq_factor = min(total_freq / 10.0, 1.0)

        # Success ratio: how often this action succeeds
        if total_exact > 0:
            success_ratio = successes / total_exact
        else:
            success_ratio = 0.5  # no data, neutral

        # Recency: check if we've seen this recently (within 7 days)
        most_recent = max((m["speed_ms"] or 0 for m in exact_matches), default=0)
        recency_factor = 1.0 if total_exact > 0 else 0.0

        # Combined confidence: weighted average
        confidence = round(
            0.3 * freq_factor +
            0.5 * success_ratio +
            0.2 * recency_factor,
            3
        )

        # Build the context injection
        context = {
            "action_hash": action_hash,
            "warnings": warnings[:3],      # Top 3 warnings
            "proven_approaches": approaches[:2],  # Top 2 proven approaches
            "has_history": len(exact_matches) > 0,
            "past_failure_count": failures,
            "past_success_count": successes,
            "confidence": confidence,  # 0.0-1.0, high = we know what will happen
            "skill_candidate": confidence > 0.70 and successes >= 2 and total_freq >= 3,
        }

        return context

    # ── AFTER ACTION: Record experience ──

    def after_action(self, action_type: str, detail: str = "",
                     result: str = "unknown", error: str = "",
                     lesson: str = "", approach: str = "",
                     fix_command: str = "", speed_ms: int = 0,
                     extra: str = "", context_tags: str = "") -> Dict:
        """
        Call AFTER any action completes. Records the experience.
        This is the "look at where you just walked" function.

        result: 'success' | 'failure' | 'partial'
        error: the raw error output (we extract the pattern)
        lesson: what to remember (auto-generated if empty and result=failure)
        approach: what approach was used
        fix_command: the command that fixed it (if failure then success)
        speed_ms: how long the action took
        """
        action_hash = self._hash_action(action_type, detail, extra)
        error_hash = self._hash_error(error) if error else ""
        now = time.time()

        # Extract error pattern (the reusable part, not the specifics)
        error_pattern = self._extract_error_pattern(error) if error else ""

        # Auto-generate lesson from error if not provided
        if not lesson and result == "failure" and error:
            lesson = self._auto_lesson(action_type, error)

        # Check if we've seen this exact pattern before
        existing = self.conn.execute(
            "SELECT id, frequency, result, iterations, lesson FROM experiences WHERE action_hash = ?",
            (action_hash,)
        ).fetchone()
        # sqlite3.Row supports dict-like access, but be defensive
        if existing is not None and not hasattr(existing, '__getitem__'):
            existing = dict(existing) if hasattr(existing, 'keys') else None

        if existing:
            # UPDATE: we've been here before
            freq = existing["frequency"] + 1
            old_result = existing["result"]

            if old_result == "failure" and result == "success":
                # WE LEARNED! Failed before, succeeded now.
                # This is the most valuable experience — record the fix.
                self.conn.execute(
                    """UPDATE experiences SET
                       result = ?, lesson = ?, approach = ?, fix_command = ?,
                       error_pattern = ?, error_snippet = ?,
                       frequency = ?, iterations = iterations + 1,
                       speed_ms = ?, last_seen = ?, context_tags = ?
                       WHERE id = ?""",
                    (result, lesson, approach, fix_command,
                     error_pattern, error[:200],
                     freq, speed_ms, now, context_tags,
                     existing["id"])
                )
                learned = True
            elif old_result == "success" and result == "failure":
                # REGRESSION! We were doing it right, now it broke.
                # Keep the old lesson but note the regression.
                updated_lesson = f"REGRESSION: Was working, now fails. {lesson}"
                self.conn.execute(
                    """UPDATE experiences SET
                       result = 'regression', lesson = ?,
                       error_pattern = ?, error_snippet = ?,
                       frequency = ?, last_seen = ?
                       WHERE id = ?""",
                    (updated_lesson, error_pattern, error[:200],
                     freq, now, existing["id"])
                )
                learned = True
            else:
                # Same result — just update frequency and timing
                self.conn.execute(
                    """UPDATE experiences SET
                       frequency = ?, last_seen = ?, speed_ms = ?,
                       lesson = COALESCE(NULLIF(?, ''), lesson)
                       WHERE id = ?""",
                    (freq, now, speed_ms, lesson, existing["id"])
                )
                learned = False
        else:
            # NEW experience
            self.conn.execute(
                """INSERT INTO experiences
                   (action_hash, action_type, action_detail, action_fingerprint,
                    result, error_pattern, error_snippet, lesson, approach,
                    fix_command, iterations, frequency, speed_ms,
                    last_seen, created_at, context_tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?)""",
                (action_hash, action_type, detail[:200], detail[:50],
                 result, error_pattern, error[:200], lesson, approach,
                 fix_command, speed_ms,
                 now, now, context_tags)
            )
            learned = False

        self.conn.commit()

        # Track for session learning (cap at 100 to prevent unbounded growth)
        self._session_actions.append({
            "type": action_type,
            "result": result,
            "learned": learned,
            "hash": action_hash,
        })
        if len(self._session_actions) > 100:
            self._session_actions = self._session_actions[-50:]

        return {
            "recorded": True,
            "new_learning": learned,
            "action_hash": action_hash,
            "total_experience_freq": (existing["frequency"] + 1) if existing else 1,
        }

    # ── BATCH: Record a complete fix sequence ──

    def record_fix_sequence(self, action_type: str, detail: str,
                            attempts: List[Dict]) -> str:
        """
        Record a multi-attempt fix sequence.
        attempts: [{attempt, command, result, error, speed_ms}, ...]

        Returns a consolidated lesson.
        """
        if not attempts:
            return ""

        total_attempts = len(attempts)
        failed = [a for a in attempts if a.get("result") == "failure"]
        succeeded = [a for a in attempts if a.get("result") == "success"]

        if succeeded:
            # The winning approach
            winner = succeeded[-1]
            lesson = f"Fix took {total_attempts} attempts. Working approach: {winner.get('command', '')[:100]}"
            if failed:
                failed_approaches = "; ".join(
                    f"attempt {a.get('attempt', '?')}: {a.get('error', '')[:60]}" for a in failed[:3]
                )
                lesson += f" | Failed: {failed_approaches}"

            self.after_action(
                action_type=action_type,
                detail=detail,
                result="success",
                lesson=lesson,
                approach=winner.get("command", "")[:200],
                fix_command=winner.get("command", ""),
                speed_ms=sum(a.get("speed_ms", 0) for a in attempts),
            )
            return lesson
        else:
            # Still broken
            lesson = f"UNRESOLVED after {total_attempts} attempts."
            self.after_action(
                action_type=action_type,
                detail=detail,
                result="failure",
                error=failed[-1].get("error", "") if failed else "unknown",
                lesson=lesson,
                speed_ms=sum(a.get("speed_ms", 0) for a in attempts),
            )
            return lesson

    # ── PATTERN EXTRACTION ──

    def _extract_error_pattern(self, error) -> str:
        """Extract the reusable pattern from an error, stripping specifics."""
        if not error:
            return ""
        
        # Ensure error is a string (may be passed as dict from mega_wiring)
        if isinstance(error, dict):
            error = json.dumps(error, default=str)
        elif not isinstance(error, str):
            error = str(error)

        # Common error patterns to detect
        patterns = [
            # TypeScript/JavaScript
            (r"TypeError: Cannot read propert(y|ies) of undefined", "TS: undefined access"),
            (r"TypeError: .+ is not a function", "TS: not-a-function call"),
            (r"SyntaxError: Unexpected token", "TS: syntax error"),
            (r"error TS\d+: ", "TS: compiler error"),
            (r"Module not found: Error: Can't resolve '([^']+)'", "TS: missing module"),
            (r"ENOENT: no such file or directory", "FS: file not found"),
            (r"Permission denied", "FS: permission denied"),

            # Python
            (r"ImportError: cannot import name '([^']+)'", "PY: import error"),
            (r"ModuleNotFoundError: No module named '([^']+)'", "PY: missing module"),
            (r"IndentationError:", "PY: indentation error"),
            (r"TypeError: .+ got an unexpected keyword argument", "PY: wrong kwargs"),
            (r"KeyError: '?([^']+)'?", "PY: missing key"),
            (r"AttributeError: '([^']+)' object has no attribute '([^']+)'", "PY: missing attribute"),

            # Git
            (r"CONFLICT.*Merge conflict in (.+)", "GIT: merge conflict"),
            (r"fatal: not a git repository", "GIT: not a repo"),
            (r"error: pathspec '([^']+)' did not match", "GIT: bad branch"),

            # Docker
            (r"Cannot connect to the Docker daemon", "DOCKER: daemon down"),
            (r"port is already allocated", "DOCKER: port conflict"),

            # General
            (r"timeout|timed out", "TIMEOUT"),
            (r"Connection refused|Connection reset", "NETWORK: connection refused"),
            (r"401|Unauthorized", "AUTH: unauthorized"),
            (r"403|Forbidden", "AUTH: forbidden"),
            (r"404|Not Found", "HTTP: not found"),
            (r"429|Too Many Requests", "HTTP: rate limited"),
            (r"500|Internal Server Error", "HTTP: server error"),
        ]

        for regex, label in patterns:
            if re.search(regex, error, re.IGNORECASE):
                return label

        # Fallback: first 100 chars, stripped of specifics
        cleaned = error[:100]
        cleaned = re.sub(r'/[^\s]+', '<path>', cleaned)
        cleaned = re.sub(r'\d+', 'N', cleaned)
        return cleaned

    def _auto_lesson(self, action_type: str, error: str) -> str:
        """Auto-generate a lesson from a failure."""
        pattern = self._extract_error_pattern(error)

        lessons_map = {
            "TS: undefined access": "Check for null/undefined before property access. Use optional chaining (?.)",
            "TS: not-a-function call": "Verify the import exists and is the correct type before calling",
            "TS: syntax error": "Check for missing brackets, semicolons, or template literal syntax",
            "TS: compiler error": "Run tsc --noEmit to see the full error before patching",
            "TS: missing module": "Check if the module is installed. Run npm/pnpm install if needed",
            "FS: file not found": "Verify the file path exists before reading. Use Path.exists()",
            "FS: permission denied": "Check file permissions. May need chmod or different directory",
            "PY: import error": "Check the module exports the name. Verify __init__.py. Check Python version compatibility",
            "PY: missing module": "Install the module with pip. Check requirements.txt",
            "PY: indentation error": "Use consistent spaces (4). Check for mixed tabs and spaces",
            "PY: wrong kwargs": "Check the function signature. May need to update after API changes",
            "PY: missing key": "Use .get() with default or check key existence with 'in'",
            "PY: missing attribute": "Check the class definition. May need __init__ assignment",
            "GIT: merge conflict": "Resolve conflicts manually. Check both sides before choosing",
            "TIMEOUT": "Increase timeout or break the task into smaller steps",
            "NETWORK: connection refused": "Check if the service is running. Verify port and host",
            "AUTH: unauthorized": "Refresh credentials. Check token expiry",
            "HTTP: rate limited": "Add delay between requests. Implement backoff",
        }

        return lessons_map.get(pattern, f"Avoid: {pattern}")

    # ── SPEED TRACKING ──

    def get_speed_trend(self, action_type: str, limit: int = 10) -> Dict:
        """
        Get the speed trend for an action type.
        Are we getting faster? This is the proof of iteration.
        """
        rows = self.conn.execute(
            """SELECT speed_ms, result, last_seen FROM experiences
               WHERE action_type = ? AND speed_ms > 0
               ORDER BY last_seen DESC LIMIT ?""",
            (action_type, limit)
        ).fetchall()

        if len(rows) < 2:
            return {"trend": "insufficient_data", "samples": len(rows)}

        speeds = [r["speed_ms"] for r in rows if r["result"] == "success"]
        if len(speeds) < 2:
            return {"trend": "no_successful_runs", "samples": len(rows)}

        # Compare recent vs earlier
        recent = speeds[:len(speeds)//2] if len(speeds) >= 4 else speeds[:1]
        earlier = speeds[len(speeds)//2:] if len(speeds) >= 4 else speeds[1:]

        avg_recent = sum(recent) / len(recent)
        avg_earlier = sum(earlier) / len(earlier)

        if avg_earlier == 0:
            return {"trend": "baseline", "avg_ms": avg_recent}

        improvement = (avg_earlier - avg_recent) / avg_earlier * 100

        return {
            "trend": "faster" if improvement > 0 else "slower",
            "improvement_pct": round(improvement, 1),
            "avg_recent_ms": round(avg_recent),
            "avg_earlier_ms": round(avg_earlier),
            "samples": len(speeds),
        }

    # ── INSIGHTS ──

    def get_learning_stats(self) -> Dict:
        """Get overall learning statistics."""
        total = self.conn.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]
        failures = self.conn.execute("SELECT COUNT(*) FROM experiences WHERE result = 'failure'").fetchone()[0]
        successes = self.conn.execute("SELECT COUNT(*) FROM experiences WHERE result = 'success'").fetchone()[0]
        regressions = self.conn.execute("SELECT COUNT(*) FROM experiences WHERE result = 'regression'").fetchone()[0]
        resolved = self.conn.execute(
            "SELECT COUNT(*) FROM experiences WHERE frequency > 1 AND result = 'success'"
        ).fetchone()[0]

        # Most common errors
        common_errors = self.conn.execute(
            """SELECT error_pattern, COUNT(*) as cnt FROM experiences
               WHERE error_pattern != '' GROUP BY error_pattern
               ORDER BY cnt DESC LIMIT 10"""
        ).fetchall()

        # Top learned lessons (successes with high frequency = patterns we've mastered)
        mastered = self.conn.execute(
            """SELECT action_type, approach, frequency, speed_ms FROM experiences
               WHERE result = 'success' AND frequency > 2
               ORDER BY frequency DESC LIMIT 10"""
        ).fetchall()

        return {
            "total_experiences": total,
            "failures": failures,
            "successes": successes,
            "regressions": regressions,
            "resolved_patterns": resolved,
            "common_errors": [(r["error_pattern"], r["cnt"]) for r in common_errors],
            "mastered_patterns": [(r["action_type"], r["frequency"], r["speed_ms"]) for r in mastered],
            "session_actions": len(self._session_actions),
            "session_learnings": sum(1 for a in self._session_actions if a.get("learned")),
        }

    def close(self):
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None


# ════════════════════════════════════════════════════════════════
# INTEGRATION HELPERS
# ════════════════════════════════════════════════════════════════

# Global singleton — import and use across modules
_engine = None
_engine_lock = threading.Lock()
_thread_local = threading.local()

def get_engine() -> IterationEngine:
    """Get a thread-local iteration engine (each thread gets its own SQLite connection)."""
    if not hasattr(_thread_local, 'engine') or _thread_local.engine is None:
        _thread_local.engine = IterationEngine()
    return _thread_local.engine


def quick_before(action_type: str, detail: str = "") -> str:
    """
    One-liner for before-action check. Returns lessons as a string
    ready to inject into any context/prompt.
    """
    engine = get_engine()
    ctx = engine.before_action(action_type, detail)

    parts = []

    if not ctx["has_history"] and not parts:
        return ""

    if ctx["warnings"]:
        parts.append("PAST FAILURES TO AVOID:")
        for w in ctx["warnings"][:2]:
            parts.append("  - %s (happened %dx)" % (w["lesson"], w["frequency"]))

    if ctx.get("proven_approaches"):
        parts.append("PROVEN APPROACHES:")
        for a in ctx["proven_approaches"][:2]:
            parts.append("  - %s (worked %dx, ~%dms)" % (a["approach"], a["frequency"], a["speed_ms"]))

    confidence = ctx.get("confidence", 0)
    if confidence > 0:
        parts.append("CONFIDENCE: %.0f%%" % (confidence * 100))
        if ctx.get("skill_candidate"):
            parts.append("  -> High-confidence pattern. Consider saving as skill.")

    return "\n".join(parts) if parts else ""


def quick_after(action_type: str, detail: str = "", result: str = "unknown",
                error: str = "", lesson: str = "", speed_ms: int = 0) -> Dict:
    """One-liner for after-action recording."""
    engine = get_engine()
    return engine.after_action(action_type, detail, result, error, lesson,
                              speed_ms=speed_ms)


if __name__ == "__main__":
    print("=== ITERATION ENGINE — STATUS ===\n")
    engine = IterationEngine()
    stats = engine.get_learning_stats()

    print(f"Total experiences recorded: {stats['total_experiences']}")
    print(f"  Successes: {stats['successes']}")
    print(f"  Failures:  {stats['failures']}")
    print(f"  Regressions: {stats['regressions']}")
    print(f"  Resolved patterns: {stats['resolved_patterns']}")

    if stats['common_errors']:
        print("\nMost common error patterns:")
        for pattern, count in stats['common_errors'][:5]:
            print(f"  {pattern}: {count}x")

    if stats['mastered_patterns']:
        print("\nMastered patterns (high-frequency successes):")
        for atype, freq, speed in stats['mastered_patterns'][:5]:
            print(f"  {atype}: {freq}x successful, ~{speed}ms")

    engine.close()
    print("\nEngine ready. Import and use quick_before()/quick_after().")
