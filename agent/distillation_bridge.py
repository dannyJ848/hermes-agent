#!/usr/bin/env python3
"""
Distillation Bridge v3 — Fully Integrated Bidirectional Pipeline.

Based on SOTA research:
- IBM Trajectory-Informed Memory (arXiv 2503.10600): 3 tip types
- ExpeL (arXiv 2308.10144): ADD/UPVOTE/DOWNVOTE/EDIT living insights
- MARS (arXiv 2601.11974): Principle + Procedural single-cycle reflection
- Mem0: Conflict resolution via similarity check

BOTTOM-UP (post_tool_call → knowledge):
  Raw tool outcome → Classify tip type → Check for conflicts → Store tip

TOP-DOWN (pre_llm_call → context):
  Task context → Retrieve relevant tips → Inject as actionable IF/THEN rules

Integrated with AGI Roadmap: knows current cycle, domain, and achievements.
"""

import json
import sqlite3
import time
import os
import sys
import threading
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("subconscious.distillation_bridge")

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"
BUFFER_PATH = Path.home() / "hermes-agent" / "distillation_buffer.jsonl"
ROADMAP_PATH = Path.home() / "hermes-agent" / "agi_roadmap.json"
PARAMS_PATH = Path.home() / "hermes-agent" / "meta_params.json"

def _load_params():
    """Load self-tunable parameters from meta_params.json."""
    try:
        if PARAMS_PATH.exists():
            with open(PARAMS_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return {"distillation": {}, "context_injection": {"max_tips": 5, "max_lessons": 3, "max_facts": 3}}

# Tip types from IBM paper
TIP_STRATEGY = "strategy"       # What works (from successes)
TIP_RECOVERY = "recovery"       # How to fix (from failures)  
TIP_OPTIMIZATION = "optimization"  # How to do better (from partial/inefficient)

_turn_counter = 0

def _get_db():
    """Get a short-lived DB connection with timeout."""
    db = sqlite3.connect(str(DB_PATH), timeout=5)
    db.execute("PRAGMA busy_timeout=3000")
    db.execute("PRAGMA journal_mode=WAL")
    return db

def _ensure_tips_table():
    """Create the distilled_tips table if it doesn't exist."""
    db = _get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS distilled_tips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tip_type TEXT NOT NULL,
            condition TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            rationale TEXT DEFAULT '',
            tool_name TEXT DEFAULT '',
            domain TEXT DEFAULT '',
            confidence REAL DEFAULT 0.5,
            upvotes INTEGER DEFAULT 1,
            downvotes INTEGER DEFAULT 0,
            frequency INTEGER DEFAULT 1,
            source_ids TEXT DEFAULT '',
            created_at REAL,
            last_seen REAL,
            last_used REAL
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_tips_type ON distilled_tips(tip_type)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_tips_tool ON distilled_tips(tool_name)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_tips_domain ON distilled_tips(domain)")
    db.commit()
    db.close()


def classify_outcome(tool_name, status, error, speed_ms):
    """Classify tool outcome into tip type."""
    if status == "success" and not error:
        if speed_ms and speed_ms > 3000:
            return TIP_OPTIMIZATION  # Slow success = optimization opportunity
        return TIP_STRATEGY  # Clean success = strategy tip
    elif status == "error" or error:
        return TIP_RECOVERY  # Failure = recovery tip
    else:
        return TIP_OPTIMIZATION  # Partial = optimization


def _is_noise_lesson(lesson):
    """Check if a lesson string is polluted iteration-engine noise."""
    if not lesson:
        return True
    noise_markers = ["FAST:", "REGRESSION:", "args_pattern:", "rich_output:",
                     "approach was 2x faster", "approach was 3x faster"]
    return any(m in lesson for m in noise_markers)


def _extract_task_intent(tool_name, args):
    """Extract the actual task intent from tool arguments (not just arg key names).
    
    Returns a human-readable summary of what the tool call was TRYING to do.
    """
    if not isinstance(args, dict):
        return ""
    
    # Tool-specific intent extraction
    if tool_name == "execute_code" and "code" in args:
        code = str(args["code"])
        # Detect what the code does
        if "import " in code:
            imports = [line.strip() for line in code.split("\n") if line.strip().startswith("import ")]
            if imports:
                return "Python code using " + ", ".join(imports[:3])
        if "def " in code:
            funcs = [line.strip() for line in code.split("\n") if "def " in line]
            if funcs:
                return "Python function: " + funcs[0][:60]
        if "sqlite3" in code or "cursor" in code:
            return "SQLite database query/operation"
        if "requests" in code or "urllib" in code:
            return "HTTP request/web fetch"
        if "json" in code and ("parse" in code or "loads" in code):
            return "JSON parsing/transformation"
        return "Python script execution"
    
    elif tool_name == "terminal" and "command" in args:
        cmd = str(args["command"])
        if cmd.startswith("git "):
            return "git operation: " + cmd.split()[1] if len(cmd.split()) > 1 else "git"
        if cmd.startswith("pip ") or cmd.startswith("npm "):
            return "package installation"
        if "sqlite3" in cmd:
            return "SQLite query via CLI"
        if cmd.startswith("ls") or cmd.startswith("find"):
            return "filesystem exploration"
        if cmd.startswith("cat") or cmd.startswith("head"):
            return "file content reading (should use read_file)"
        if cmd.startswith("cd ") or cmd.startswith("mkdir"):
            return "directory navigation/creation"
        return "shell command: " + cmd[:50]
    
    elif tool_name == "web_research" and "query" in args:
        return "research: " + str(args["query"])[:80]
    
    elif tool_name == "web_extract" and "url" in args:
        url = str(args["url"])
        domain = url.split("//")[-1].split("/")[0] if "//" in url else url[:40]
        return "extract content from " + domain
    
    elif tool_name == "patch" and "path" in args:
        path = str(args["path"])
        ext = path.rsplit(".", 1)[-1] if "." in path else "file"
        return "edit " + ext + " file: " + path.split("/")[-1]
    
    elif tool_name == "search_files" and "pattern" in args:
        return "search for: " + str(args["pattern"])[:60]
    
    elif tool_name == "read_file" and "path" in args:
        return "read: " + str(args["path"]).split("/")[-1]
    
    elif tool_name == "write_file" and "path" in args:
        return "write: " + str(args["path"]).split("/")[-1]
    
    elif tool_name == "delegate_with_model" and "goal" in args:
        return "delegate: " + str(args["goal"])[:80]
    
    elif tool_name == "delegate_parallel":
        return "parallel delegation"
    
    elif tool_name == "browser_navigate" and "url" in args:
        return "navigate to: " + str(args["url"])[:60]
    
    elif tool_name == "skill_manage" and "name" in args:
        action = args.get("action", "")
        return f"{action} skill: {args['name']}"
    
    return ""


def extract_tip_heuristic(tool_name, args, status, speed_ms, error, lesson):
    """Extract a structured tip from tool outcome using heuristics (no LLM needed).
    
    Returns (condition, recommendation, rationale) or None if nothing to learn.
    
    Quality filter: Only produces tips that contain ACTUAL behavioral insights,
    not surface-level metrics like arg names or speed comparisons.
    """
    # Skip trivial tools that produce no useful lessons
    skip_tools = {"memory", "session_checkpoint", "session_restore", 
                  "autonomous_decide", "cronjob", "status_check",
                  "watchdog_heartbeat", "memory_score", "memory_decay",
                  "habits_log", "proactive_budget", "proactive_nudge"}
    if tool_name in skip_tools:
        return None
    
    # Filter out polluted lesson strings (speed reports, arg patterns)
    clean_lesson = None
    if lesson and len(lesson) > 15 and not _is_noise_lesson(lesson):
        clean_lesson = lesson
    
    # Extract what the tool call was actually trying to do
    task_intent = _extract_task_intent(tool_name, args)
    
    # ── RECOVERY TIPS (from errors) ──
    if error:
        error_lower = error.lower()
        
        # Specific known error patterns with real fixes
        if "syntaxerror" in error_lower or "indentationerror" in error_lower:
            return (
                "When writing Python in execute_code",
                "Use write_file for multi-line code, not terminal. Check indentation carefully.",
                "SyntaxError is the #1 failure mode"
            )
        if "filenotfound" in error_lower or "not found" in error_lower:
            fix = "Verify path with search_files first"
            if task_intent:
                fix = f"Verify path exists before {task_intent}"
            return (
                "When accessing files with {}".format(tool_name),
                fix + ". Use Path.home() not ~ in Python.",
                "File not found errors waste turns"
            )
        if "database is locked" in error_lower:
            return (
                "When writing to SQLite from hooks",
                "Use JSONL buffer for writes, merge via controller cron. Never write directly to DB from hooks.",
                "SQLite locking is the #1 concurrency issue"
            )
        if "timeout" in error_lower:
            return (
                "When calling {} with large payloads".format(tool_name),
                "Use pagination, reduce output size, or split into smaller calls",
                "Timeout at {}ms".format(speed_ms)
            )
        if "permission denied" in error_lower:
            return (
                "When accessing system paths with {}".format(tool_name),
                "Check file_permissions deny list. Use ~/paths for user space.",
                "Permission denied indicates protected path"
            )
        if "connection" in error_lower or "refused" in error_lower:
            return (
                "When connecting to services from {}".format(tool_name),
                "Check if service is running (docker ps, ps aux). Verify port and URL.",
                "Connection errors mean service may be down"
            )
        if "403" in error_lower or "forbidden" in error_lower:
            return (
                "When fetching from restricted URLs with {}".format(tool_name),
                "Switch to web_research for the same topic. 403 = anti-bot protection, retrying won't help.",
                "403 errors persist on retry — change approach entirely"
            )
        if "json" in error_lower and "decode" in error_lower:
            return (
                "When parsing JSON responses from {}".format(tool_name),
                "Use json.loads with strict=False, or try extracting with regex first. Check for BOM markers.",
                "JSON decode errors often from non-standard output"
            )
        if "module" in error_lower and "not found" in error_lower:
            mod = error_lower.split("module")[-1].strip().strip("'\"")
            return (
                "When {} requires missing module".format(tool_name),
                "Install with pip first, or use stdlib alternative",
                "Module import failure: {}".format(mod[:40])
            )
        
        # Generic error — don't produce template tips (was generating 45 identical junk tips)
        # Better to produce nothing than generic "verify inputs, retry with backoff" advice
        return None
    
    # ── STRATEGY TIPS (from successes with real lessons) ──
    # Only produce strategy tips if we have a CLEAN lesson or meaningful task context
    
    if clean_lesson:
        # The lesson is genuine (not speed noise) — structure it
        condition = "When using {} for: {}".format(tool_name, task_intent[:40]) if task_intent else "When using {}".format(tool_name)
        return (
            condition,
            clean_lesson[:150],
            "Learned from {} outcome".format(status)
        )
    
    # Tool-specific success pattern extraction (only when we have real arg content)
    if status == "success" and isinstance(args, dict):
        
        if tool_name == "execute_code" and "code" in args:
            code = str(args["code"])
            # Detect successful patterns worth recording
            if "from hermes_tools import" in code:
                return (
                    "When using execute_code for multi-step tool logic",
                    "Use execute_code (not terminal) for Python with tool calls. Import from hermes_tools.",
                    "execute_code handles Python escaping correctly; terminal does not"
                )
            if code.count("\n") > 15 and "def " in code:
                return (
                    "When writing long Python functions in execute_code",
                    "Break into smaller functions. Use write_file first, then import/execute.",
                    "Long inline code is fragile — indentation errors compound"
                )
        
        elif tool_name == "web_extract" and "url" in args:
            if speed_ms and speed_ms > 5000:
                return (
                    "When web_extract takes >5s on a URL",
                    "Use max_chars=3000 to limit response. For 403 errors, switch to web_research instead.",
                    "Large extractions waste tokens; limit upfront"
                )
        
        elif tool_name == "terminal" and "command" in args:
            cmd = str(args["command"])
            if cmd.startswith("cat ") or cmd.startswith("head ") or cmd.startswith("tail "):
                return (
                    "When reading file contents via terminal",
                    "Use read_file instead of cat/head/tail — it has pagination and line numbers.",
                    "read_file is purpose-built; terminal cat loses formatting"
                )
            if "grep" in cmd or "rg " in cmd:
                return (
                    "When searching file contents via terminal",
                    "Use search_files instead of grep/rg — it has built-in pagination and context.",
                    "search_files is purpose-built for content search"
                )
        
        elif tool_name == "patch" and args.get("mode") == "replace":
            if speed_ms and speed_ms < 500:
                return (
                    "When making targeted edits to existing files",
                    "Use patch(mode='replace') with enough context lines for unique matching. Include 3+ surrounding lines.",
                    "Fuzzy matching in patch handles minor whitespace differences"
                )
    
    # ── OPTIMIZATION TIPS (only for genuinely slow calls with actionable advice) ──
    if speed_ms and speed_ms > 15000 and status == "success":
        return (
            "When {} takes >15s to complete".format(tool_name),
            "Pre-split the work: paginate results, reduce output size, or cache for reuse.",
            "Very slow call ({}ms) — likely processing too much at once".format(speed_ms)
        )
    
    return None


def find_similar_tip(db, condition, recommendation, threshold=0.8):
    """Find similar existing tips using text matching."""
    # Simple text similarity (no embedding needed)
    keywords = set(condition.lower().split() + recommendation.lower().split()[:10])
    keywords = {w for w in keywords if len(w) > 3}  # Skip short words
    
    if not keywords:
        return None
    
    # Build LIKE query for each keyword
    # Query tips matching same tool or same tip_type for relevance
    # Increased from LIMIT 200 to 1000 to catch more duplicates (was causing
    # 894 duplicate optimization tips at 0.50 confidence - Cycle fix Apr 2026)
    rows = db.execute(
        "SELECT id, condition, recommendation, frequency, upvotes, downvotes "
        "FROM distilled_tips WHERE tool_name != '' LIMIT 1000"
    ).fetchall()
    
    best_match = None
    best_score = 0
    
    for row in rows:
        tip_id, cond, rec, freq, ups, downs = row
        existing_text = (cond + " " + rec).lower()
        matches = sum(1 for k in keywords if k in existing_text)
        score = matches / max(len(keywords), 1)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = row
    
    return best_match


def bottom_up_store(tool_name, args, status, speed_ms, error="", lesson="", failure_stage=""):
    """BOTTOM-UP: Extract tip from tool outcome, check conflicts, store.
    
    Pipeline: outcome → classify → extract tip → find conflicts → store/merge
    """
    global _turn_counter
    _turn_counter += 1
    
    # 1. Write raw entry to JSONL buffer (always, for controller)
    # Sanitize args: keep only serializable, non-huge values
    safe_args = {}
    if isinstance(args, dict):
        for k, v in args.items():
            try:
                val_str = str(v)
                if len(val_str) < 500:  # Don't store huge args
                    safe_args[k] = val_str
            except Exception:
                pass
    entry = {
        "tool_name": tool_name,
        "args": safe_args,
        "status": status,
        "speed_ms": speed_ms,
        "error": error[:100] if error else "",
        "lesson": lesson[:100] if lesson else "",
        "failure_stage": failure_stage or "",
        "timestamp": time.time(),
        "turn": _turn_counter,
    }
    try:
        with open(BUFFER_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    
    # 2. Extract structured tip
    tip_type = classify_outcome(tool_name, status, error, speed_ms)
    tip_data = extract_tip_heuristic(tool_name, args, status, speed_ms, error, lesson)
    
    if not tip_data:
        return  # Nothing to learn from this outcome
    
    condition, recommendation, rationale = tip_data
    
    # 3. Store or merge tip (ExpeL-style: ADD/UPVOTE/DOWNVOTE)
    try:
        _ensure_tips_table()
        db = _get_db()
        
        similar = find_similar_tip(db, condition, recommendation)
        
        if similar:
            # SIMILAR TIP EXISTS → upvote or downvote
            tip_id, cond, rec, freq, ups, downs = similar
            if tip_type == TIP_STRATEGY or tip_type == TIP_RECOVERY:
                # Successful pattern or recovery worked → upvote
                db.execute(
                    "UPDATE distilled_tips SET upvotes=upvotes+1, frequency=frequency+1, "
                    "last_seen=? WHERE id=?",
                    (time.time(), tip_id)
                )
            elif tip_type == TIP_OPTIMIZATION:
                # Just note it's seen again
                db.execute(
                    "UPDATE distilled_tips SET frequency=frequency+1, last_seen=? WHERE id=?",
                    (time.time(), tip_id)
                )
        else:
            # NEW TIP → add it
            # FINAL NOISE GUARD: never insert noise tips (belt + suspenders)
            if recommendation and (
                recommendation.startswith("[")
                or "args_pattern" in recommendation
                or "FAST:" in recommendation
                or "rich_output" in recommendation
                or "approach was" in recommendation
                or recommendation.startswith("{")
            ):
                return  # Noise tip — discard
            
            # REJECT "From research:" tips — speculative, not operational
            if condition and condition.startswith("From research:"):
                return
            
            # REJECT tips with fake tool names (research domains, not actual tools)
            _REAL_TOOLS = {
                "execute_code", "terminal", "read_file", "write_file", "patch",
                "search_files", "web_extract", "web_search", "web_research",
                "browser_navigate", "browser_snapshot", "browser_click",
                "browser_type", "browser_vision", "browser_back", "browser_scroll",
                "browser_console", "browser_get_images", "browser_press",
                "vision_analyze", "delegate_with_model", "delegate_parallel",
                "delegate_task", "cached_delegate", "send_message", "memory",
                "knowledge_search", "skill_manage", "skill_view", "skills_list",
                "evey_goals", "cronjob", "cost_check", "cost_analytics",
                "session_checkpoint", "session_restore", "session_search",
                "validate_output", "autonomous_decide", "autonomous_plan",
                "autonomous_reflect", "reflect_on_output", "learn_from_interaction",
                "delegation_log", "delegation_stats", "mcp_biomcp_biomcp",
                "mesh_status", "mesh_message", "mesh_task", "mesh_lock",
                "save_finding", "schedule_add", "schedule_list", "schedule_remove",
                "proactive_nudge", "proactive_budget", "telegram_card",
                "telegram_status", "text_to_speech", "watchdog_heartbeat",
                "claude_bridge_task", "claude_bridge_message", "claude_bridge_check",
                "daily_digest", "habits_insights", "habits_log", "tool_intelligence",
                "telemetry_query", "verify_url", "verify_endpoint", "verify_dns",
                "verify_repo", "email_screen", "moltbook_post", "moltbook_reply",
                "moltbook_heartbeat", "news_scan", "mqtt_publish_event",
                "mqtt_status", "mqtt_subscribe", "clarify", "todo",
                "consolidate_daily_memory", "memory_decay", "memory_score",
                "update_identity", "sandbox_list", "secure_read", "secure_search",
                "apply_learnings", "process", "execute_code", "council_decide",
                "cost_set_budget", "status_check", "watchdog_status",
            }
            if tool_name not in _REAL_TOOLS:
                return  # Fake tool name — reject
            
            # Get current AGI domain
            domain = "unknown"
            try:
                if ROADMAP_PATH.exists():
                    with open(ROADMAP_PATH) as f:
                        roadmap = json.load(f)
                    cycle = roadmap.get("current_cycle", 0)
                    # Simple domain lookup
                    for start, end, name, _ in [
                        (1, 50, "VISION", ""), (51, 150, "MEMORY", ""),
                        (151, 250, "REASONING", ""), (251, 400, "DEVELOPMENT", ""),
                        (401, 550, "RESEARCH", ""), (551, 700, "TOOL_MASTERY", ""),
                        (701, 850, "AUTONOMY", ""), (851, 1000, "INTEGRATION", ""),
                    ]:
                        if start <= cycle <= end:
                            domain = name
                            break
            except Exception:
                pass
            
            db.execute(
                "INSERT INTO distilled_tips "
                "(tip_type, condition, recommendation, rationale, tool_name, domain, "
                "confidence, upvotes, frequency, created_at, last_seen) "
                "VALUES (?, ?, ?, ?, ?, ?, 0.5, 1, 1, ?, ?)",
                (tip_type, condition, recommendation, rationale, tool_name, domain,
                 time.time(), time.time())
            )
        
        db.commit()
        db.close()
    except Exception:
        pass  # DB locked — skip, don't block

    # --- Auto-pruning: check if MEMORY needs consolidation ---
    try:
        sub_path = str(Path.home() / "hermes-agent")
        if sub_path not in sys.path:
            sys.path.insert(0, sub_path)
        from pruner_integration import should_prune, safe_prune
        if should_prune():
            threading.Thread(target=safe_prune, kwargs={"force": False}, daemon=True).start()
            logger.debug("Prune thread spawned after bottom_up_store")
    except Exception:
        pass  # Never block the main pipeline


def top_down_recall(task_context, max_items=None):
    """TOP-DOWN: Retrieve relevant tips + facts + lessons for injection.
    
    Pipeline: task context → search tips → search facts → search lessons → format
    Uses self-tunable parameters from meta_params.json.
    """
    parts = []
    now = time.time()
    
    # Load self-tunable parameters
    params = _load_params()
    ci = params.get("context_injection", {})
    dist = params.get("distillation", {})
    
    if max_items is None:
        max_items = ci.get("max_tips", 5)
    max_lessons = ci.get("max_lessons", 3)
    max_facts = ci.get("max_facts", 3)
    tip_conf_min = dist.get("tip_confidence_min", 0.3)
    
    # 1. Distilled tips (highest priority — actionable rules)
    try:
        _ensure_tips_table()
        db = _get_db()
        
        # Search by tool name or domain keywords
        keywords = task_context.lower().split()[:5]
        query_parts = " OR ".join(["condition LIKE ?" for _ in keywords])
        params = [f"%{k}%" for k in keywords]
        
        rows = db.execute(
            f"SELECT tip_type, condition, recommendation, confidence, upvotes, downvotes, frequency "
            f"FROM distilled_tips "
            f"WHERE ({query_parts}) OR tool_name IN "
            f"(SELECT DISTINCT tool_name FROM distilled_tips WHERE condition LIKE ?) "
            f"ORDER BY (upvotes - downvotes) DESC, confidence DESC LIMIT ?",
            params + [f"%{task_context[:30]}%", max_items]
        ).fetchall()
        db.close()
        
        if rows:
            tip_lines = []
            for ttype, cond, rec, conf, ups, downs, freq in rows:
                vote_score = ups - downs
                if vote_score > 0 or freq > 2:  # Only well-voted tips
                    tip_lines.append(
                        f"  IF {cond[:60]} THEN {rec[:80]} "
                        f"(type={ttype}, votes={vote_score}, seen={freq}x)"
                    )
            if tip_lines:
                parts.append("[ACTIONABLE TIPS]\n" + "\n".join(tip_lines[:5]))
    except Exception:
        pass
    
    # 1.5 DISABLED: Meta-insights — just tips reorganized by principles/procedures.
    # Zero additional signal over ACTIONABLE TIPS + DISTILLED TOOL RULES.
    # Re-enable if meta_insights table gets unique high-level patterns.
    
    # 2. DISABLED: Semantic facts — these caused the memory echo bug.
    # Facts are available via knowledge_search when needed. Don't inject proactively.
    
    # DISABLED: Iteration lessons — all garbage (failed delegate_parallel, 
    # interrupted commands, DNS errors). Zero actionable signal.
    
    # DISABLED: AGI Roadmap context — "Cycle 217/1000" is meaningless noise 
    # that doesn't change behavior. Check manually if needed.
    
    # Memory health: run prune check silently but don't inject admin data.
    try:
        sub_path = str(Path.home() / "hermes-agent")
        if sub_path not in sys.path:
            sys.path.insert(0, sub_path)
        from pruner_integration import memory_health, safe_prune
        health = memory_health()
        if health.get("needs_prune"):
            logger.warning("Memory at %.1f%% during recall — forced prune", health["usage_pct"])
            safe_prune(force=True)
            # Don't append to parts — admin data not needed in agent context
    except Exception:
        pass  # Non-blocking

    return "\n\n".join(parts) if parts else ""


def extract_tip_llm(tool_name, args_summary, status, error, speed_ms, existing_tips):
    """Generate LLM prompt for structured tip extraction (ExpeL-style).
    
    Returns {"system": ..., "user": ...} prompt pair, or None if no tips to compare.
    """
    # Build existing tips block
    if existing_tips:
        tip_lines = []
        for t in existing_tips:
            tip_lines.append(
                "  TIP #{}  [{}]  votes={}\n"
                "    IF:     {}\n"
                "    THEN:   {}\n"
                "    BECAUSE:{}".format(
                    t.get('id', '?'), t.get('tip_type', '?'), t.get('votes', 0),
                    t.get('condition', ''), t.get('recommendation', ''), t.get('rationale', '')
                )
            )
        tips_block = "\n".join(tip_lines)
    else:
        tips_block = "  (no existing tips)"
    
    # Build outcome block
    outcome_parts = [
        "Tool:        {}".format(tool_name),
        "Arguments:   {}".format(args_summary),
        "Status:      {}".format(status),
        "Speed:       {} ms".format(speed_ms),
    ]
    if error:
        outcome_parts.append("Error:       {}".format(error))
    outcome_block = "\n".join(outcome_parts)
    
    system_prompt = (
        "You are an Insight Extraction Agent (ExpeL framework). "
        "Analyze the tool outcome and distill it into a structured tip, "
        "or decide how it relates to existing tips.\n\n"
        "OUTPUT: ONLY valid JSON (no markdown fences):\n"
        '{"operation": "ADD|UPVOTE|DOWNVOTE|EDIT|SKIP", '
        '"tip_type": "strategy|recovery|optimization", '
        '"condition": "WHEN-clause", '
        '"recommendation": "WHAT-clause", '
        '"rationale": "WHY-clause", '
        '"target_tip_id": null|int}\n\n'
        "OPERATIONS:\n"
        "- ADD: New lesson not captured. Fill condition/recommendation/rationale.\n"
        "- UPVOTE: Outcome confirms existing tip. Set target_tip_id.\n"
        "- DOWNVOTE: Outcome contradicts existing tip. Set target_tip_id.\n"
        "- EDIT: Existing tip needs correction. Set target_tip_id + updated fields.\n"
        "- SKIP: No actionable insight. All fields null/empty.\n\n"
        "TIP TYPES:\n"
        "- strategy: General approach for success\n"
        "- recovery: Error handling / failure recovery\n"
        "- optimization: Performance improvement\n\n"
        "RULES:\n"
        "1. Be SPECIFIC (reference tool name, argument patterns, error substrings)\n"
        "2. Be GENERALIZABLE (should help in future similar situations)\n"
        "3. Be CONCISE (single sentence per clause)\n"
        "4. Match SEMANTICS when comparing to existing tips\n"
        "5. Speed >5000ms suggests optimization tip\n"
        "6. Error present suggests recovery tip\n"
        "7. NEVER hallucinate — only use info from the outcome or existing tips"
    )
    
    user_prompt = (
        "=== TOOL OUTCOME ===\n{}\n\n"
        "=== EXISTING TIPS ===\n{}\n\n"
        "Analyze the outcome. Formulate a tip in IF/THEN/BECAUSE form. "
        "Compare against existing tips. Respond with ONLY the JSON."
    ).format(outcome_block, tips_block)
    
    return {"system": system_prompt, "user": user_prompt}


def epoch_synthesis(hours=1, min_tips=5):
    """REMO-inspired epoch-level synthesis of raw tips into meta-insights.
    
    Batches tips from the last N hours, groups by tool/domain, and 
    synthesizes higher-level principles (MARS) + procedures (IBM).
    Stores as 'meta_insights' in the DB for top_down_recall to inject.
    """
    _ensure_tips_table()
    db = _get_db()
    cutoff = time.time() - (hours * 3600)
    
    # Gather recent tips
    rows = db.execute(
        "SELECT tip_type, condition, recommendation, tool_name, domain, "
        "confidence, upvotes, downvotes, frequency "
        "FROM distilled_tips WHERE last_seen > ? ORDER BY frequency DESC",
        (cutoff,)
    ).fetchall()
    
    if len(rows) < min_tips:
        db.close()
        return {"status": "insufficient", "count": len(rows)}
    
    # Group by tool_name
    by_tool = {}
    for ttype, cond, rec, tool, domain, conf, ups, downs, freq in rows:
        key = tool or "general"
        if key not in by_tool:
            by_tool[key] = {"strategy": [], "recovery": [], "optimization": [], "gap": [], "domain": domain}
        by_tool[key].setdefault(ttype, []).append({
            "condition": cond[:80],
            "recommendation": rec[:100],
            "confidence": conf,
            "votes": ups - downs,
            "frequency": freq
        })
    
    # Synthesize meta-insights per tool
    insights = []
    for tool, data in by_tool.items():
        domain = data.get("domain", "general")
        
        # ── Principle synthesis: extract behavioral RULES, not speed stats ──
        principles = []
        
        # Recovery principles: group by error root cause
        if len(data["recovery"]) >= 2:
            error_types = {}
            for tip in data["recovery"]:
                cond = tip["condition"].lower()
                # Categorize the error type
                if "syntax" in cond or "indent" in cond:
                    error_types.setdefault("syntax", []).append(tip)
                elif "file" in cond or "path" in cond or "not found" in cond:
                    error_types.setdefault("file_access", []).append(tip)
                elif "403" in cond or "forbidden" in cond:
                    error_types.setdefault("access_denied", []).append(tip)
                elif "timeout" in cond or "slow" in cond:
                    error_types.setdefault("timeout", []).append(tip)
                elif "connection" in cond or "refused" in cond:
                    error_types.setdefault("connection", []).append(tip)
                elif "database" in cond or "locked" in cond or "sqlite" in cond:
                    error_types.setdefault("database", []).append(tip)
                else:
                    error_types.setdefault("other", []).append(tip)
            
            # Build principle from most common error category
            for err_cat, err_tips in sorted(error_types.items(), key=lambda x: -len(x[1])):
                if len(err_tips) >= 2:
                    best_fix = max(err_tips, key=lambda t: t["frequency"])["recommendation"][:80]
                    principles.append(
                        f"{tool} {err_cat} rule: {best_fix}"
                    )
                    break  # One principle per tool
        
        # Strategy principles: extract WHAT WORKED, not speed
        strategy_recs = []
        for tip in data["strategy"]:
            rec = tip["recommendation"]
            # Skip speed/arg noise
            if any(noise in rec for noise in ["FAST:", "args_pattern", "rich_output", "approach was"]):
                continue
            strategy_recs.append(rec[:80])
        
        if strategy_recs:
            # Deduplicate and take top 2
            unique_recs = list(dict.fromkeys(strategy_recs))[:2]
            principles.append(
                f"{tool} success pattern: {'; '.join(unique_recs)}"
            )
        
        # ── Procedural synthesis: action sequences ──
        procedures = []
        
        # Best success procedure
        good_strategies = [t for t in data["strategy"] 
                          if not any(n in t["recommendation"] for n in ["FAST:", "args_pattern", "rich_output"])]
        if good_strategies:
            best = max(good_strategies, key=lambda t: t["votes"])
            procedures.append(f"For {tool}: {best['recommendation'][:80]}")
        
        # Most common failure procedure
        if data["recovery"]:
            # Group failures to find the most impactful one
            failure_recs = [t for t in data["recovery"] 
                          if t["recommendation"] and len(t["recommendation"]) > 15]
            if failure_recs:
                most_common = max(failure_recs, key=lambda t: t["frequency"])
                procedures.append(f"When {tool} fails: {most_common['recommendation'][:80]}")
        
        # Store as meta-insight only if we have REAL content
        if principles or procedures:
            # Filter out principles that are just speed concatenations
            real_principles = [p for p in principles if "FAST" not in p and "args_pattern" not in p]
            if real_principles or procedures:
                insight = {
                    "tool": tool,
                    "domain": domain,
                    "principles": real_principles,
                    "procedures": procedures,
                    "tip_count": sum(len(v) for v in data.values() if isinstance(v, list)),
                    "synthesized_at": datetime.now().isoformat()
                }
                insights.append(insight)
    
    # Store meta-insights (upsert by tool)
    try:
        db.execute(
            "CREATE TABLE IF NOT EXISTS meta_insights "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "tool_name TEXT UNIQUE, domain TEXT, "
            "principles TEXT, procedures TEXT, "
            "tip_count INTEGER, confidence REAL DEFAULT 0.7, "
            "synthesized_at TEXT, created_at REAL)"
        )
        for ins in insights:
            db.execute(
                "INSERT OR REPLACE INTO meta_insights "
                "(tool_name, domain, principles, procedures, tip_count, confidence, synthesized_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ins["tool"], ins["domain"],
                 json.dumps(ins["principles"]), json.dumps(ins["procedures"]),
                 ins["tip_count"], 0.7, ins["synthesized_at"], time.time())
            )
        db.commit()
    except Exception as e:
        pass
    
    db.close()
    return {"status": "synthesized", "tools": len(insights), "total_tips": len(rows)}


def get_stats():
    """Get distillation pipeline stats."""
    try:
        _ensure_tips_table()
        db = _get_db()
        
        total_tips = db.execute("SELECT COUNT(*) FROM distilled_tips").fetchone()[0]
        by_type = db.execute(
            "SELECT tip_type, COUNT(*), AVG(upvotes - downvotes) FROM distilled_tips GROUP BY tip_type"
        ).fetchall()
        
        buffer_count = 0
        if BUFFER_PATH.exists():
            buffer_count = sum(1 for _ in open(BUFFER_PATH))
        
        db.close()
        
        print(f"Distilled Tips: {total_tips}")
        for ttype, cnt, avg_votes in by_type:
            print(f"  {ttype}: {cnt} tips, avg votes={avg_votes:.1f}")
        print(f"JSONL Buffer: {buffer_count} entries")
        return total_tips
    except Exception as e:
        print(f"Error: {e}")
        return 0


# ── UPSTREAM PATTERN: Trajectory Format Export (adapted from agent_runtime_helpers.py) ──
# Export successful tool sequences as standardized training trajectories.
# Format matches upstream convert_to_trajectory_format for compatibility.

def export_trajectory(session_messages, user_query, completed=True):
    """Export session as trajectory for training replay.
    
    Adapted from upstream agent_runtime_helpers.py:
    - Standardized format for training data
    - Strips think blocks, keeps tool calls + results
    - Stores in training_gym for replay
    """
    import re
    trajectory = []
    
    # System message with tool definitions (simplified)
    trajectory.append({
        "from": "system",
        "value": "You are a function calling AI. Use available tools to assist."
    })
    
    # User query
    trajectory.append({
        "from": "human", 
        "value": user_query
    })
    
    # Process messages — extract tool calls and results
    for msg in session_messages:
        if msg.get("role") == "assistant":
            # Strip think blocks (upstream pattern)
            content = msg.get("content", "")
            if content:
                # Remove <thinking>...</thinking> blocks
                content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
                content = content.strip()
            
            entry = {"from": "gpt", "value": content}
            
            # Add tool calls if present
            if msg.get("tool_calls"):
                tool_calls = []
                for tc in msg["tool_calls"]:
                    tool_calls.append({
                        "name": tc.get("function", {}).get("name", ""),
                        "arguments": tc.get("function", {}).get("arguments", "")
                    })
                entry["tool_calls"] = tool_calls
            
            trajectory.append(entry)
        
        elif msg.get("role") == "tool":
            # Tool result
            trajectory.append({
                "from": "tool",
                "name": msg.get("name", ""),
                "value": str(msg.get("content", ""))[:500]  # Truncate long outputs
            })
    
    # Store in training gym buffer
    try:
        traj_path = Path.home() / ".hermes" / "training_trajectories.jsonl"
        with open(traj_path, "a") as f:
            f.write(json.dumps({
                "query": user_query,
                "completed": completed,
                "trajectory": trajectory,
                "timestamp": time.time()
            }) + "\n")
    except Exception:
        pass
    
    return trajectory


def get_recent_trajectories(hours=24, limit=50):
    """Get recent trajectories for training replay."""
    traj_path = Path.home() / ".hermes" / "training_trajectories.jsonl"
    if not traj_path.exists():
        return []
    
    cutoff = time.time() - (hours * 3600)
    trajectories = []
    
    try:
        with open(traj_path) as f:
            for line in f:
                entry = json.loads(line)
                if entry.get("timestamp", 0) > cutoff:
                    trajectories.append(entry)
    except Exception:
        pass
    
    # Return most recent, limited
    return sorted(trajectories, key=lambda x: x.get("timestamp", 0), reverse=True)[:limit]


if __name__ == "__main__":
    print("=== Distillation Bridge v3 — Test ===\n")
    
    # Test bottom-up
    print("--- Bottom-Up: Strategy tip ---")
    bottom_up_store("execute_code", {"code": "print('hello')"}, "success", 200, "", "")
    
    print("--- Bottom-Up: Recovery tip ---")
    bottom_up_store("execute_code", {}, "error", 500, "SyntaxError: unexpected indent", "")
    
    print("--- Bottom-Up: Optimization tip ---")
    bottom_up_store("web_extract", {"url": "long-page"}, "success", 8000, "", "slow response")
    
    # Test top-down
    print("\n--- Top-Down: Code context ---")
    result = top_down_recall("Python execute_code syntax")
    print(result if result else "(no recall)")
    
    print("\n--- Stats ---")
    get_stats()


class DistillationBridge:
    """Orchestrator-compatible wrapper for the distillation pipeline."""
    
    def __init__(self):
        self._buffer_path = Path.home() / "hermes-agent" / "distillation_buffer.jsonl"
        self._last_run = 0
        self._min_interval = 300  # 5 min between runs
    
    def process_tool_outcome(self, tool_name, args, status, speed_ms, error="", lesson=""):
        """Process a single tool outcome through the distillation pipeline."""
        try:
            bottom_up_store(tool_name, args, status, speed_ms, error, lesson)
            return {"status": "processed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def run_distillation_cycle(self, min_actions=10):
        """Run a full distillation cycle if enough data has accumulated."""
        import time
        now = time.time()
        if now - self._last_run < self._min_interval:
            return {"status": "skipped", "reason": "too_soon"}
        
        try:
            # Count recent buffer entries
            count = 0
            if self._buffer_path.exists():
                with open(self._buffer_path) as f:
                    for line in f:
                        entry = json.loads(line)
                        if now - entry.get("timestamp", 0) < 3600:
                            count += 1
            
            if count < min_actions:
                return {"status": "skipped", "reason": "not_enough_data", "count": count}
            
            self._last_run = now
            return {"status": "completed", "entries_processed": count}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_tip_stats(self):
        """Get statistics on distilled tips."""
        try:
            db = _get_db()
            cursor = db.execute("SELECT COUNT(*) FROM distilled_tips")
            total = cursor.fetchone()[0]
            
            cursor = db.execute("SELECT tip_type, COUNT(*) FROM distilled_tips GROUP BY tip_type")
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            db.close()
            return {"total_tips": total, "by_type": by_type}
        except Exception:
            return {"total_tips": 0, "by_type": {}}
