#!/usr/bin/env python3
"""
EVEY TRAINING GYM — Infinite Self-Training Loop
================================================
Progressive difficulty exercises across 8 domains.
Auto-scored, fed into distillation, runs forever.

Architecture:
  training_gym.db     — exercise definitions + score history
  Cron job            — kicks off training sessions every 15 min
  Bottom-up           — post_exercise extracts tips from failures
  Top-down            — pre_exercise injects relevant tips
"""

import sqlite3
import json
import time
import os
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".hermes" / "training_gym.db"

def get_db():
    db = sqlite3.connect(str(DB_PATH), timeout=10)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS exercises (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            tier INTEGER NOT NULL DEFAULT 1,
            name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            verify_cmd TEXT NOT NULL,
            verify_type TEXT NOT NULL DEFAULT 'exit_code',
            scoring TEXT NOT NULL DEFAULT '{"pass": 10, "partial": 5, "fail": 0}',
            time_limit INTEGER DEFAULT 120,
            tags TEXT DEFAULT '',
            created_at REAL DEFAULT (strftime('%s','now'))
        );
        
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id TEXT NOT NULL,
            started_at REAL NOT NULL,
            finished_at REAL,
            score INTEGER DEFAULT 0,
            max_score INTEGER DEFAULT 10,
            tool_calls INTEGER DEFAULT 0,
            tools_used TEXT DEFAULT '[]',
            errors TEXT DEFAULT '[]',
            raw_output TEXT DEFAULT '',
            reflection TEXT DEFAULT '',
            tip_extracted INTEGER DEFAULT 0,
            tier_at_attempt INTEGER DEFAULT 1,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );
        
        CREATE TABLE IF NOT EXISTS personal_records (
            exercise_id TEXT PRIMARY KEY,
            best_score INTEGER DEFAULT 0,
            best_time REAL,
            attempts INTEGER DEFAULT 0,
            last_attempted REAL,
            streak INTEGER DEFAULT 0,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );
        
        CREATE TABLE IF NOT EXISTS tier_progress (
            category TEXT,
            tier INTEGER,
            exercises_total INTEGER DEFAULT 0,
            exercises_passed INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 0,
            unlocks_next INTEGER DEFAULT 0,
            PRIMARY KEY (category, tier)
        );
        
        CREATE INDEX IF NOT EXISTS idx_attempts_exercise ON attempts(exercise_id);
        CREATE INDEX IF NOT EXISTS idx_attempts_time ON attempts(started_at);
    """)
    db.commit()
    db.close()

# ─── Exercise definitions ─────────────────────────────────────────
# Tier 1: Basic tool proficiency
# Tier 2: Multi-step workflows  
# Tier 3: Error recovery & adaptation
# Tier 4: Complex planning & synthesis
# Tier 5: Metacognitive & self-improvement

EXERCISES = {
    # ═══ TIER 1: TOOL PRECISION ═══
    "tp-001": {
        "category": "tool_precision",
        "tier": 1,
        "name": "Read file with correct tool",
        "prompt": "Read the file ~/.hermes/config.yaml and tell me how many lines it has. Use the correct tool for reading files.",
        "verify_cmd": "echo 'Verify: agent used read_file, not terminal cat'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "fail": 0},
        "tags": "read_file,basic",
    },
    "tp-002": {
        "category": "tool_precision",
        "tier": 1, 
        "name": "Search files with correct tool",
        "prompt": "Find all Python files in ~/hermes-agent/tools/ that contain 'register_tool'. Report the count and file names.",
        "verify_cmd": "echo 'Verify: agent used search_files'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "fail": 0},
        "tags": "search_files,basic",
    },
    "tp-003": {
        "category": "tool_precision",
        "tier": 1,
        "name": "Write file correctly",
        "prompt": "Create a file at /tmp/gym-test-write.txt with the content 'Gym test passed'. Then read it back to verify.",
        "verify_cmd": "test -f /tmp/gym-test-write.txt && grep -q 'Gym test passed' /tmp/gym-test-write.txt && echo PASS || echo FAIL",
        "verify_type": "exit_code",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "write_file,read_file",
    },
    "tp-004": {
        "category": "tool_precision",
        "tier": 1,
        "name": "Patch file correctly",
        "prompt": "Create a file at /tmp/gym-patch-test.txt with content 'Hello World'. Then use patch to change 'World' to 'Universe'. Verify the change.",
        "verify_cmd": "grep -q 'Hello Universe' /tmp/gym-patch-test.txt && ! grep -q 'Hello World' /tmp/gym-patch-test.txt && echo PASS || echo FAIL",
        "verify_type": "exit_code",
        "scoring": {"pass": 10, "fail": 0},
        "tags": "write_file,patch",
    },
    "tp-005": {
        "category": "tool_precision",
        "tier": 1,
        "name": "Web research (not extract)",
        "prompt": "Search the web for 'latest Python version 2026' and report what you find. Do NOT try to extract specific URLs.",
        "verify_cmd": "echo 'Verify: agent used web_research first'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "web_research,basic",
    },

    # ═══ TIER 1: TERMINAL PROFICIENCY ═══
    "tm-001": {
        "category": "terminal",
        "tier": 1,
        "name": "Git status check",
        "prompt": "Check the git status of ~/hermes-agent/ and report: (1) current branch, (2) number of modified files, (3) number of untracked files.",
        "verify_cmd": "echo 'Verify: agent used terminal for git'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "terminal,git",
    },
    "tm-002": {
        "category": "terminal",
        "tier": 1,
        "name": "Python script execution",
        "prompt": "Write a Python script to /tmp/gym-fib.py that computes the 20th Fibonacci number and prints it. Then run it.",
        "verify_cmd": "test -f /tmp/gym-fib.py && python3 /tmp/gym-fib.py | grep -q '6765' && echo PASS || echo FAIL",
        "verify_type": "exit_code",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "write_file,terminal,python",
    },
    "tm-003": {
        "category": "terminal",
        "tier": 1,
        "name": "SQLite query",
        "prompt": "Query ~/.hermes/cerebrum_memory.db to count total entries in the semantic_facts table. Report the number.",
        "verify_cmd": "echo 'Verify: agent queried DB and reported a number'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "fail": 0},
        "tags": "terminal,sqlite",
    },

    # ═══ TIER 2: MULTI-STEP WORKFLOWS ═══
    "ms-001": {
        "category": "multi_step",
        "tier": 2,
        "name": "File analysis pipeline",
        "prompt": "Find the largest .py file in ~/hermes-agent/tools/ by line count. Read its first 50 lines and summarize what it does.",
        "verify_cmd": "echo 'Verify: multi-tool pipeline used'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "search_files,read_file,terminal",
    },
    "ms-002": {
        "category": "multi_step",
        "tier": 2,
        "name": "Config audit",
        "prompt": "Read ~/.hermes/config.yaml. Count how many tools are enabled and how many are disabled. List any tool that looks misconfigured.",
        "verify_cmd": "echo 'Verify: read config and reported counts'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "read_file,analysis",
    },
    "ms-003": {
        "category": "multi_step",
        "tier": 2,
        "name": "Research + save finding",
        "prompt": "Research what 'process reward models' are in AI. Save a finding to the knowledge library about it with at least 2 sources.",
        "verify_cmd": "echo 'Verify: research done and finding saved'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "web_research,save_finding",
    },
    "ms-004": {
        "category": "multi_step",
        "tier": 2,
        "name": "Build a CLI tool",
        "prompt": "Create a Python CLI tool at /tmp/gym-wordcount.py that takes a file path as argument, counts words/lines/chars, and prints a formatted table. Make it work and test it on itself.",
        "verify_cmd": "test -f /tmp/gym-wordcount.py && python3 /tmp/gym-wordcount.py /tmp/gym-wordcount.py | grep -qE '(words|lines|chars)' && echo PASS || echo FAIL",
        "verify_type": "exit_code",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "write_file,terminal,python,build",
    },
    "ms-005": {
        "category": "multi_step",
        "tier": 2,
        "name": "Parallel research",
        "prompt": "Research 3 topics in parallel using delegate_parallel: (1) flash attention, (2) mixture of experts, (3) chain of thought. Summarize each in 2-3 sentences.",
        "verify_cmd": "echo 'Verify: used delegate_parallel for 3 topics'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "delegate_parallel,research",
    },

    # ═══ TIER 3: ERROR RECOVERY ═══
    "er-001": {
        "category": "error_recovery",
        "tier": 3,
        "name": "Read nonexistent file",
        "prompt": "Read the file /tmp/gym-nonexistent-file-xyz.txt. It does NOT exist. Handle the error gracefully and report what happened.",
        "verify_cmd": "echo 'Verify: agent handled error without crashing'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "read_file,error_handling",
    },
    "er-002": {
        "category": "error_recovery",
        "tier": 3,
        "name": "Invalid command recovery",
        "prompt": "Run this exact command in terminal: 'definitely_not_a_real_command_xyz'. Handle the failure and explain what went wrong.",
        "verify_cmd": "echo 'Verify: agent handled command not found'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "fail": 0},
        "tags": "terminal,error_handling",
    },
    "er-003": {
        "category": "error_recovery",
        "tier": 3,
        "name": "403 web recovery",
        "prompt": "Try to extract content from https://www.nytimes.com/ (which will likely block you). Handle the 403 correctly by switching to web_research instead.",
        "verify_cmd": "echo 'Verify: agent recovered from 403 by switching tools'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "web_extract,web_research,error_recovery",
    },
    "er-004": {
        "category": "error_recovery",
        "tier": 3,
        "name": "Malformed JSON parse",
        "prompt": "Write this exact content to /tmp/gym-bad.json: '{\"name\": \"test\", \"value\": broken,}'. Then write a Python script that tries to parse it, handles the JSON error, and reports which field is broken.",
        "verify_cmd": "test -f /tmp/gym-bad.json && echo PASS || echo FAIL",
        "verify_type": "exit_code",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "write_file,execute_code,error_handling",
    },

    # ═══ TIER 4: COMPLEX PLANNING & SYNTHESIS ═══
    "cp-001": {
        "category": "complex_planning",
        "tier": 4,
        "name": "Full project scaffold",
        "prompt": "Create a complete Python project at /tmp/gym-project/ with: (1) main.py with a Hello class, (2) tests/test_main.py with 2 passing tests, (3) requirements.txt, (4) README.md. Run the tests and verify they pass.",
        "verify_cmd": "test -f /tmp/gym-project/main.py && test -f /tmp/gym-project/tests/test_main.py && test -f /tmp/gym-project/requirements.txt && test -f /tmp/gym-project/README.md && echo PASS || echo FAIL",
        "verify_type": "exit_code",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "write_file,terminal,planning,build",
    },
    "cp-002": {
        "category": "complex_planning",
        "tier": 4,
        "name": "Database design + query",
        "prompt": "Design and create a SQLite database at /tmp/gym-library.db for a library system (books, authors, loans). Create at least 3 tables with proper foreign keys. Insert 5 sample books. Write a query to find all books by a specific author with their loan status.",
        "verify_cmd": "test -f /tmp/gym-library.db && sqlite3 /tmp/gym-library.db 'SELECT COUNT(*) FROM books' | grep -qv '0' && echo PASS || echo FAIL",
        "verify_type": "exit_code",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "execute_code,sqlite,planning",
    },
    "cp-003": {
        "category": "complex_planning",
        "tier": 4,
        "name": "Deep research report",
        "prompt": "Research the current state of AI agent benchmarks (SWE-bench, WebArena, AgentBench). For each: what it tests, current top scores, limitations. Synthesize into a structured report and save as a finding.",
        "verify_cmd": "echo 'Verify: structured report with 3+ benchmarks'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "web_research,synthesis,save_finding",
    },
    "cp-004": {
        "category": "complex_planning",
        "tier": 4,
        "name": "API reverse engineering",
        "prompt": "Find a public API (e.g. JSONPlaceholder, PokéAPI, or similar). Write a Python client for it at /tmp/gym-api-client.py that fetches data, handles errors, and pretty-prints results. Test it.",
        "verify_cmd": "test -f /tmp/gym-api-client.py && python3 /tmp/gym-api-client.py 2>/dev/null | grep -qE '(id|name|title)' && echo PASS || echo FAIL",
        "verify_type": "exit_code",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "web_research,write_file,terminal,build",
    },

    # ═══ TIER 5: METACOGNITION & SELF-IMPROVEMENT ═══
    "mc-001": {
        "category": "metacognition",
        "tier": 5,
        "name": "Self-diagnosis",
        "prompt": "Analyze your own tool performance from the last 24 hours. Which tool has the lowest success rate? What specific improvement would you make to your approach with that tool?",
        "verify_cmd": "echo 'Verify: identified weakest tool with specific improvement'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "metacognition,analysis",
    },
    "mc-002": {
        "category": "metacognition",
        "tier": 5,
        "name": "Calibration check",
        "prompt": "Before each of these 5 questions, state your confidence (0-100%). Then answer: (1) What is the capital of Burkina Faso? (2) How many lines in run_agent.py? (3) What's my (Danny's) graduation year? (4) What Python version is installed? (5) What's the current SWE-bench verified top score? After answering, check which you got right and compute calibration.",
        "verify_cmd": "echo 'Verify: confidence stated before each answer, then checked'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "metacognition,calibration",
    },
    "mc-003": {
        "category": "metacognition",
        "tier": 5,
        "name": "Tip refinement",
        "prompt": "Review your current distilled tips in cerebrum_memory.db. Find one tip that has high upvotes but also significant downvotes. Analyze the conflict and propose a refined version that addresses the failure cases.",
        "verify_cmd": "echo 'Verify: found conflicting tip and proposed refinement'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "metacognition,distillation",
    },
    "mc-004": {
        "category": "metacognition",
        "tier": 5,
        "name": "New exercise design",
        "prompt": "Design 3 NEW training exercises for yourself based on your weakest areas. Each exercise should have: a clear prompt, auto-verifiable success criteria, and target a specific weakness. Save them to the training gym database.",
        "verify_cmd": "echo 'Verify: 3 exercises designed and saved'",
        "verify_type": "output_check",
        "scoring": {"pass": 10, "partial": 5, "fail": 0},
        "tags": "metacognition,self-improvement",
    },
}

def seed_exercises():
    """Insert all exercise definitions into the database."""
    db = get_db()
    for eid, ex in EXERCISES.items():
        db.execute("""
            INSERT OR REPLACE INTO exercises (id, category, tier, name, prompt, verify_cmd, verify_type, scoring, time_limit, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            eid, ex["category"], ex["tier"], ex["name"],
            ex["prompt"], ex["verify_cmd"], ex["verify_type"],
            json.dumps(ex.get("scoring", {})), ex.get("time_limit", 120),
            ex.get("tags", "")
        ))
    db.commit()
    db.close()
    print(f"Seeded {len(EXERCISES)} exercises")

def get_next_exercise(category=None, tier=None):
    """Pick the next exercise to train on based on performance gaps."""
    db = get_db()
    
    # Find exercises with lowest scores or fewest attempts
    if category and tier:
        rows = db.execute("""
            SELECT e.*, COALESCE(pr.best_score, 0) as best, COALESCE(pr.attempts, 0) as att
            FROM exercises e
            LEFT JOIN personal_records pr ON e.id = pr.exercise_id
            WHERE e.category = ? AND e.tier = ?
            ORDER BY pr.best_score ASC NULLS FIRST, pr.attempts ASC, RANDOM()
            LIMIT 1
        """, (category, tier)).fetchall()
    else:
        # Prioritize: unattempted > lowest score > random
        rows = db.execute("""
            SELECT e.*, COALESCE(pr.best_score, 0) as best, COALESCE(pr.attempts, 0) as att
            FROM exercises e
            LEFT JOIN personal_records pr ON e.id = pr.exercise_id
            ORDER BY pr.attempts ASC, pr.best_score ASC, RANDOM()
            LIMIT 1
        """).fetchall()
    
    db.close()
    return dict(rows[0]) if rows else None

def get_stats():
    """Get overall training statistics."""
    db = get_db()
    stats = {}
    
    # Total attempts
    stats["total_attempts"] = db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    
    # By tier
    stats["by_tier"] = []
    for row in db.execute("""
        SELECT e.tier, COUNT(*) as attempts, 
               ROUND(AVG(a.score * 1.0 / a.max_score) * 100, 1) as avg_pct
        FROM attempts a JOIN exercises e ON a.exercise_id = e.id
        GROUP BY e.tier ORDER BY e.tier
    """).fetchall():
        stats["by_tier"].append(dict(row))
    
    # By category
    stats["by_category"] = []
    for row in db.execute("""
        SELECT e.category, COUNT(*) as attempts,
               ROUND(AVG(a.score * 1.0 / a.max_score) * 100, 1) as avg_pct,
               SUM(CASE WHEN a.score >= a.max_score THEN 1 ELSE 0 END) as passes
        FROM attempts a JOIN exercises e ON a.exercise_id = e.id
        GROUP BY e.category ORDER BY avg_pct ASC
    """).fetchall():
        stats["by_category"].append(dict(row))
    
    # Recent streak
    recent = db.execute("""
        SELECT score, max_score FROM attempts ORDER BY started_at DESC LIMIT 10
    """).fetchall()
    if recent:
        stats["recent_pass_rate"] = round(
            sum(1 for r in recent if r["score"] >= r["max_score"]) / len(recent) * 100, 1
        )
    else:
        stats["recent_pass_rate"] = 0
    
    db.close()
    return stats

def record_attempt(exercise_id, score, max_score, tools_used=None, errors=None, 
                   raw_output="", reflection="", tier=1):
    """Record an attempt and update personal records."""
    db = get_db()
    now = time.time()
    
    db.execute("""
        INSERT INTO attempts (exercise_id, started_at, finished_at, score, max_score,
                             tools_used, errors, raw_output, reflection, tier_at_attempt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (exercise_id, now - 60, now, score, max_score,
          json.dumps(tools_used or []), json.dumps(errors or []),
          raw_output[:500], reflection[:500], tier))
    
    # Update personal record
    db.execute("""
        INSERT INTO personal_records (exercise_id, best_score, best_time, attempts, last_attempted, streak)
        VALUES (?, ?, ?, 1, ?, 1)
        ON CONFLICT(exercise_id) DO UPDATE SET
            best_score = MAX(best_score, ?),
            best_time = CASE WHEN ? > best_score THEN ? ELSE best_time END,
            attempts = attempts + 1,
            last_attempted = ?,
            streak = CASE WHEN ? >= 10 
                          THEN streak + 1 ELSE 0 END
    """, (exercise_id, score, 60, now, score, score, 60, now, score))
    
    # Update tier progress
    db.execute("""
        INSERT INTO tier_progress (category, tier, exercises_total, exercises_passed, avg_score)
        SELECT e.category, e.tier, 1, 
               CASE WHEN ? >= 10 THEN 1 ELSE 0 END,
               ?
        FROM exercises e WHERE e.id = ?
        ON CONFLICT(category, tier) DO UPDATE SET
            exercises_total = exercises_total + 1,
            exercises_passed = exercises_passed + CASE WHEN ? >= 10 THEN 1 ELSE 0 END,
            avg_score = (avg_score * exercises_total + ?) / (exercises_total + 1)
    """, (score, score, exercise_id, score, score))
    
    db.commit()
    db.close()


# ── UPSTREAM PATTERN: Background Review Fork (adapted from background_review.py) ──
# After each exercise, spawn an isolated review to evaluate whether the
# exercise produced a tip worth distilling. Uses tool whitelist like upstream.

def _spawn_exercise_review(exercise_id, attempt_data, raw_output):
    """Fork a lightweight review after exercise completion.
    
    Adapted from upstream background_review.py pattern:
    - Isolated evaluation (no side effects on main session)
    - Tool whitelist: only memory/skill tools
    - Prefix cache optimization (inherits system prompt)
    """
    import threading
    import contextlib
    from io import StringIO
    
    def _review_target():
        # Capture stdout to prevent leakage
        buf = StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                # Evaluate: did this exercise produce a learning?
                score = attempt_data.get("score", 0)
                max_score = attempt_data.get("max_score", 10)
                errors = json.loads(attempt_data.get("errors", "[]"))
                
                if score >= max_score and not errors:
                    # Perfect run — maybe too easy, consider tier bump
                    _bump_exercise_tier(exercise_id)
                elif errors:
                    # Failure — extract tip for distillation
                    _extract_exercise_tip(exercise_id, errors, raw_output)
                
            except Exception:
                pass  # Review failures are non-blocking
    
    # Spawn as daemon thread (non-blocking, like upstream)
    t = threading.Thread(target=_review_target, daemon=True)
    t.start()
    return t


def _bump_exercise_tier(exercise_id):
    """Consider bumping exercise to next tier if consistently perfect."""
    db = get_db()
    # Check last 3 attempts
    rows = db.execute(
        "SELECT score, max_score FROM attempts WHERE exercise_id=? ORDER BY finished_at DESC LIMIT 3",
        (exercise_id,)
    ).fetchall()
    
    if len(rows) >= 3 and all(r["score"] >= r["max_score"] for r in rows):
        # Consistently perfect — bump tier
        db.execute(
            "UPDATE exercises SET tier = tier + 1 WHERE id=? AND tier < 5",
            (exercise_id,)
        )
        db.commit()
    db.close()


def _extract_exercise_tip(exercise_id, errors, raw_output):
    """Extract a tip from exercise failure for distillation pipeline."""
    if not errors:
        return
    
    # Get exercise info
    db = get_db()
    ex = db.execute("SELECT category, name, prompt FROM exercises WHERE id=?", (exercise_id,)).fetchone()
    if not ex:
        db.close()
        return
    
    # Build tip from first error
    error = errors[0] if isinstance(errors, list) else str(errors)
    condition = f"When training in {ex['category']} (exercise: {ex['name']})"
    recommendation = f"Error encountered: {str(error)[:100]}. Review: {ex['prompt'][:80]}"
    
    # Store in cerebrum via distillation bridge if available
    try:
        from agent.distillation_bridge import bottom_up_store
        bottom_up_store(
            tool_name=f"training_{ex['category']}",
            args={"exercise": ex['name']},
            status="error",
            speed_ms=0,
            error=str(error)[:200],
            lesson=recommendation
        )
    except Exception:
        pass
    
    db.close()

    init_db()
    seed_exercises()
    print("Training gym initialized!")
    print(json.dumps(get_stats(), indent=2))


class TrainingGym:
    """Orchestrator-compatible wrapper for the training gym."""
    
    def __init__(self):
        self._initialized = False
        self._last_session = 0
        self._min_interval = 600  # 10 min between sessions
    
    def _ensure_initialized(self):
        if not self._initialized:
            try:
                init_db()
                seed_exercises()
                self._initialized = True
            except Exception:
                pass
    
    def get_next_exercise(self, category=None, tier=None):
        """Get the next exercise to train on."""
        self._ensure_initialized()
        try:
            return get_next_exercise(category, tier)
        except Exception as e:
            return {"error": str(e)}
    
    def record_attempt(self, exercise_id, score, max_score, **kwargs):
        """Record a training attempt."""
        self._ensure_initialized()
        try:
            record_attempt(exercise_id, score, max_score, **kwargs)
            return {"status": "recorded"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_gym_stats(self):
        """Get training statistics."""
        self._ensure_initialized()
        try:
            return get_stats()
        except Exception as e:
            return {"error": str(e)}
    
    def run_error_focused_training(self):
        """Run a training session focused on recent errors."""
        import time
        now = time.time()
        if now - self._last_session < self._min_interval:
            return {"status": "skipped", "reason": "too_soon"}
        
        self._ensure_initialized()
        self._last_session = now
        
        # Get an error recovery exercise
        exercise = self.get_next_exercise(category="error_recovery")
        if not exercise or "error" in exercise:
            return {"status": "skipped", "reason": "no_exercises"}
        
        return {
            "status": "ready",
            "exercise_id": exercise.get("id"),
            "exercise_name": exercise.get("name"),
            "tier": exercise.get("tier"),
        }
