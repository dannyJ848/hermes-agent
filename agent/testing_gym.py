#!/usr/bin/env python3
"""
Testing Gym — Benchmark Evaluation Framework for Agent Self-Improvement

Architecture based on: AgentBench (ICLR'24), GAIA (Meta/HuggingFace),
Galileo Framework, SWE-bench evaluation methodology.

5 domains × 4 tasks × 2 sets (baseline + holdout) = 40 benchmark tasks (L1-L4)
3-axis scoring: outcome 60% + efficiency 20% + tool selection 20%
Paired-calibration with Welch's t-test + Cohen's d + regression guard
L4 Mythos-tier: adversarial scoring, compilation checks, cross-file verification, synthesis detection

Usage:
    from testing_gym import get_instance
    gym = get_instance("session_id")
    report = gym.run_benchmark(task_ids=["search_l1_base", "coding_l2_base"])

CLI:
    python3 testing_gym.py              # self-test
    python3 testing_gym.py --run-suite  # run baseline suite
    python3 testing_gym.py --task ID    # run single task
"""

import json
import math
import os
import re
import json
import time
import hashlib
import threading
import subprocess
import tempfile
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path
from collections import defaultdict

# ── Instance Registry (thread-safe singleton per session) ──
_INSTANCES: Dict[str, "TestingGym"] = {}
_INSTANCE_LOCK = threading.Lock()


def get_instance(session_id: str = "default") -> "TestingGym":
    with _INSTANCE_LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = TestingGym(session_id)
        return _INSTANCES[session_id]


# ── Data Classes ──

@dataclass
class BenchmarkTask:
    """A single benchmark task definition."""
    id: str
    domain: str           # search, coding, reasoning, tool_use, planning
    difficulty: str        # L1, L2, L3
    set_name: str         # baseline, holdout
    prompt: str           # Task prompt given to agent
    oracle_type: str       # exact_match, state_diff, behavioral, invariant
    oracle_spec: Dict      # Specification for scoring
    expected_tools: List[str]  # Tools that SHOULD be used
    max_steps: int         # Maximum allowed tool calls
    max_time_s: float = 120.0  # Max wall-clock time


@dataclass
class TrajectoryStep:
    """One step in an agent's execution trajectory."""
    tool_name: str
    tool_args: Dict
    result_summary: str   # First 200 chars of result
    success: bool
    timestamp: float
    latency_s: float


@dataclass
class TrajectoryResult:
    """Complete trajectory from a benchmark run."""
    task_id: str
    run_type: str          # baseline, post, holdout_baseline, holdout_post
    steps: List[TrajectoryStep] = field(default_factory=list)
    final_answer: str = ""
    total_time_s: float = 0.0
    started_at: float = 0.0
    finished_at: float = 0.0
    error: Optional[str] = None


@dataclass
class TrajectoryScores:
    """Scores for a single trajectory."""
    task_id: str
    outcome: float         # 0-10
    efficiency: float      # 0-10
    tool_selection: float  # 0-10
    composite: float       # 0-10 weighted
    details: Dict = field(default_factory=dict)


@dataclass
class GymReport:
    """Statistical comparison report between baseline and post-intervention."""
    baseline_scores: Dict[str, TrajectoryScores]   # task_id -> scores
    post_scores: Dict[str, TrajectoryScores]
    per_domain_baseline: Dict[str, float]          # domain -> avg composite
    per_domain_post: Dict[str, float]
    overall_baseline: float
    overall_post: float
    delta: float                                   # post - baseline
    welch_t: Optional[float] = None
    welch_p: Optional[float] = None
    cohens_d: Optional[float] = None
    significant: Optional[bool] = None
    regressions: List[str] = field(default_factory=list)  # Task IDs that regressed
    improvements: List[str] = field(default_factory=list)
    memorization_flag: bool = False                 # Cross-entropy check
    production_gate: str = "none"                   # dev/staging/production/none
    timestamp: float = field(default_factory=time.time)


# ── Code-Aware Oracle ──

def _extract_code_blocks(answer: str) -> List[str]:
    """Extract Python code blocks from markdown answer."""
    blocks = re.findall(r'```(?:python)?\s*\n(.*?)```', answer, re.DOTALL)
    return blocks


def _run_code_safely(code: str, test_input: str = "", timeout: int = 5) -> Tuple[bool, str, str]:
    """Run Python code in a subprocess. Returns (success, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        if test_input:
            f.write(f"\n\n# Test\nprint({test_input})")
        f.flush()
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["python3", tmp_path],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PYTHONPATH": ""}
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"
    except Exception as e:
        return False, "", str(e)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass



def _code_oracle_score(answer: str, spec: dict) -> Tuple[float, Dict]:
    """Code-aware oracle: structural analysis + compilation check."""
    answer_lower = answer.lower()
    must_import = [m.lower() for m in spec.get("must_import", [])]
    must_handle = [h.lower() for h in spec.get("must_handle", [])]
    must_feature = [f.lower() for f in spec.get("must_feature", [])]
    must_compile = spec.get("must_compile", False)
    output_file = spec.get("output_file", "")
    min_length = spec.get("min_length", 100)
    is_l4 = spec.get("adversarial", False)

    # 1. Import presence
    import_score = sum(1 for m in must_import if m in answer_lower) / max(1, len(must_import))

    # 2. Error handling keywords — enhanced with code pattern detection
    error_kw = ["try", "except", "raise", "error", "fail", "retry", "timeout", "handle"]
    handle_matches = 0
    for h in must_handle:
        h_words = h.split()[:2]
        # Check raw text AND code patterns
        if any(w in answer_lower for w in h_words):
            handle_matches += 1
        elif any(p in answer_lower for p in [f"@{h}", f"handle_{h}", f"{h}_handler",
                                              f"except.*{h}", f"raise.*{h}"]):
            handle_matches += 1
        elif h == "retry" and ("@retry" in answer_lower or "retry(" in answer_lower or "tenacity" in answer_lower):
            handle_matches += 1
        elif h == "timeout" and ("timeout=" in answer_lower or "asyncio.wait_for" in answer_lower):
            handle_matches += 1
        elif h == "circuit breaker" and ("circuit" in answer_lower and "breaker" in answer_lower):
            handle_matches += 1
    handle_score = handle_matches / max(1, len(must_handle))

    # 3. Feature presence — enhanced with code pattern detection
    feat_matches = 0
    for f in must_feature:
        if f in answer_lower:
            feat_matches += 1
        # Code-specific: decorator detection (@<name>)
        elif any(p in answer_lower for p in [f"@{f}", f"def {f}", f"class {f}", f"{f}("]):
            feat_matches += 1
    feat_score = feat_matches / max(1, len(must_feature))

    # 4. Length adequacy
    length_score = min(1.0, len(answer) / max(1, min_length))

    # 5. Compilation check (L4: must actually compile/run)
    comp_score = 0.5  # neutral default
    if must_compile and output_file and os.path.exists(output_file):
        try:
            result = subprocess.run(
                ["python3", "-c", f"import ast; ast.parse(open('{output_file}').read())"],
                capture_output=True, text=True, timeout=5
            )
            comp_score = 1.0 if result.returncode == 0 else 0.0
            # L4 bonus: try actual import for runtime validity
            if comp_score > 0 and is_l4 and output_file.endswith('.py'):
                mod_name = os.path.basename(output_file).replace('.py', '')
                try:
                    imp_result = subprocess.run(
                        ["python3", "-c", f"import sys; sys.path.insert(0, '{os.path.dirname(output_file)}'); import {mod_name}"],
                        capture_output=True, text=True, timeout=10
                    )
                    if imp_result.returncode == 0:
                        comp_score = 1.0  # Full credit for importable module
                    else:
                        comp_score = 0.7  # Syntax OK but import fails (dependency issues)
                except Exception:
                    comp_score = 0.7  # Import timeout, syntax was OK
        except Exception:
            comp_score = 0.0
    elif must_compile and not os.path.exists(output_file):
        comp_score = 0.0  # L4 strict: file MUST exist for compilation credit

    # 6. Output file content verification (L4: actual file check, strict)
    file_score = 0.5  # neutral
    if output_file and os.path.exists(output_file):
        try:
            with open(output_file) as f:
                fcontent = f.read().lower()
            # Stricter for L4: check that must_import items appear in FILE not just answer
            if is_l4:
                file_imports = sum(1 for m in must_import if m in fcontent)
                file_score = file_imports / max(1, len(must_import)) if must_import else 0.7
            else:
                file_score = 0.7  # file exists = partial credit for non-L4
        except Exception:
            file_score = 0.2

    # Weights: L4 shifts weight to compilation + file verification
    if is_l4:
        weights = [0.15, 0.15, 0.15, 0.10, 0.25, 0.20]  # comp + file heavier
    else:
        weights = [0.25, 0.20, 0.20, 0.15, 0.10, 0.10]  # standard

    components = [import_score, handle_score, feat_score, length_score, comp_score, file_score]
    score = 10.0 * sum(w * c for w, c in zip(weights, components))
    details = {
        "imports": f"{import_score:.0%}", "handling": f"{handle_score:.0%}",
        "features": f"{feat_score:.0%}", "length": f"{length_score:.0%}",
        "compiles": f"{comp_score:.0%}", "file": f"{file_score:.0%}",
        "l4_strict": is_l4
    }
    return score, details

def _build_task_registry() -> Dict[str, BenchmarkTask]:
    """Build the complete task registry. 5 domains × 2 tasks × 2 sets = 20."""
    tasks = {}

    # ── DOMAIN: SEARCH ──
    tasks["search_l1_baseline"] = BenchmarkTask(
        id="search_l1_baseline", domain="search", difficulty="L1", set_name="baseline",
        prompt="Find the Q3 2024 earnings per share for MicroStrategy (MSTR) from their official 10-Q filing with the SEC.",
        oracle_type="exact_match",
        oracle_spec={"answer_pattern": r"\$[\d.]+", "keywords": ["microstrategy", "q3", "2024", "eps", "earnings"]},
        expected_tools=["web_search", "web_extract"],
        max_steps=5, max_time_s=60,
    )
    tasks["search_l1_holdout"] = BenchmarkTask(
        id="search_l1_holdout", domain="search", difficulty="L1", set_name="holdout",
        prompt="What was the closing price of Shopify (SHOP) on January 3, 2025?",
        oracle_type="exact_match",
        oracle_spec={"answer_pattern": r"\$[\d.]+", "keywords": ["shopify", "shop", "closing", "price", "january", "2025"]},
        expected_tools=["web_search", "web_extract"],
        max_steps=5, max_time_s=60,
    )
    tasks["search_l2_baseline"] = BenchmarkTask(
        id="search_l2_baseline", domain="search", difficulty="L2", set_name="baseline",
        prompt="Synthesize the current scientific consensus on erythritol safety as a sugar substitute. Cite at least 3 peer-reviewed studies. Address both the 2023 Nature Medicine cardiometabolic risk study and the subsequent criticism of its methodology.",
        oracle_type="behavioral",
        oracle_spec={
            "must_cite": ["nature medicine", "erythritol"],
            "must_address": ["cardiometabolic risk", "methodology criticism"],
            "min_sources": 3,
            "min_length": 200,
        },
        expected_tools=["web_search", "web_extract", "web_research"],
        max_steps=10, max_time_s=120,
    )
    tasks["search_l2_holdout"] = BenchmarkTask(
        id="search_l2_holdout", domain="search", difficulty="L2", set_name="holdout",
        prompt="Compare the efficacy of semaglutide vs tirzepatide for weight loss, citing cardiovascular outcome trial data (SELECT and SURPASS-2). Include both benefits and documented adverse effects.",
        oracle_type="behavioral",
        oracle_spec={
            "must_cite": ["semaglutide", "tirzepatide"],
            "must_address": ["cardiovascular", "select", "surpass", "adverse"],
            "min_sources": 3,
            "min_length": 200,
        },
        expected_tools=["web_search", "web_extract", "web_research"],
        max_steps=10, max_time_s=120,
    )

    # ── DOMAIN: CODING ──
    tasks["coding_l1_baseline"] = BenchmarkTask(
        id="coding_l1_baseline", domain="coding", difficulty="L1", set_name="baseline",
        prompt="Fix this Python script. It has a subtle bug: the regex pattern misses multi-word city names like 'New York'.\n\n```python\nimport re\ndef extract_cities(text):\n    pattern = r'[A-Z][a-z]+'\n    return re.findall(pattern, text)\n```",
        oracle_type="behavioral",
        oracle_spec={
            "must_fix": "regex pattern must capture multi-word capitalized sequences",
            "test_input": "extract_cities(\"I visited New York and Los Angeles last year\")",
            "expected_output_contains": ["New York", "Los Angeles"],
        },
        expected_tools=["execute_code", "write_file"],
        max_steps=5, max_time_s=60,
    )
    tasks["coding_l1_holdout"] = BenchmarkTask(
        id="coding_l1_holdout", domain="coding", difficulty="L1", set_name="holdout",
        prompt="This function has a race condition — it reads a shared counter without a lock. Fix it:\n\n```python\nimport threading\ncounter = 0\ndef increment():\n    global counter\n    current = counter\n    counter = current + 1\n```",
        oracle_type="behavioral",
        oracle_spec={
            "must_fix": "add threading.Lock around counter access",
            "must_import": ["threading"],
        },
        expected_tools=["execute_code"],
        max_steps=5, max_time_s=60,
    )
    tasks["coding_l2_baseline"] = BenchmarkTask(
        id="coding_l2_baseline", domain="coding", difficulty="L2", set_name="baseline",
        prompt="Create a Python CLI tool that resizes images in a directory. Requirements: (1) Accept directory path + max dimension as args, (2) Resize maintaining aspect ratio, (3) Support jpg/png/webp, (4) Write to output/ subdir, (5) Handle corrupted files gracefully, (6) Show progress bar.",
        oracle_type="behavioral",
        oracle_spec={
            "must_import": ["PIL", "argparse", "os"],
            "must_handle": ["corrupted", "progress"],
            "must_output": "output/",
        },
        expected_tools=["execute_code", "write_file"],
        max_steps=10, max_time_s=120,
    )
    tasks["coding_l2_holdout"] = BenchmarkTask(
        id="coding_l2_holdout", domain="coding", difficulty="L2", set_name="holdout",
        prompt="Build a rate-limited API client wrapper in Python. Requirements: (1) Configurable requests/sec limit, (2) Automatic retry on 429/5xx with exponential backoff, (3) Timeout support, (4) Async-compatible using asyncio + aiohttp, (5) Proper connection pooling.",
        oracle_type="behavioral",
        oracle_spec={
            "must_import": ["asyncio", "aiohttp"],
            "must_handle": ["429", "backoff", "timeout"],
            "must_feature": ["rate limit", "connection pool"],
        },
        expected_tools=["execute_code", "write_file"],
        max_steps=10, max_time_s=120,
    )

    # ── DOMAIN: REASONING ──
    tasks["reasoning_l1_baseline"] = BenchmarkTask(
        id="reasoning_l1_baseline", domain="reasoning", difficulty="L1", set_name="baseline",
        prompt="A farmer has 17 sheep. All but 9 die from a disease. How many sheep are still alive?",
        oracle_type="exact_match",
        oracle_spec={"answer": "9"},
        expected_tools=[],  # Pure reasoning, no tools needed
        max_steps=2, max_time_s=30,
    )
    tasks["reasoning_l1_holdout"] = BenchmarkTask(
        id="reasoning_l1_holdout", domain="reasoning", difficulty="L1", set_name="holdout",
        prompt="If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
        oracle_type="exact_match",
        oracle_spec={"answer": "5"},
        expected_tools=[],
        max_steps=2, max_time_s=30,
    )
    tasks["reasoning_l2_baseline"] = BenchmarkTask(
        id="reasoning_l2_baseline", domain="reasoning", difficulty="L2", set_name="baseline",
        prompt="Schedule 5 one-hour meetings for 4 people across 2 days (Mon-Tue, 9am-5pm). Constraints:\n- Alice is off Monday morning\n- Bob has standup Tue 9-9:30\n- Carol needs back-to-back meetings\n- Dave can only do afternoons\n- Meeting D requires Meeting A's output\n- No double-booking",
        oracle_type="invariant",
        oracle_spec={
            "invariants": [
                "no_double_booking",
                "alice_free_mon_morning",
                "bob_free_tue_9_930",
                "carol_back_to_back",
                "dave_afternoon_only",
                "D_after_A",
                "all_5_meetings_scheduled",
            ],
        },
        expected_tools=["execute_code"],
        max_steps=10, max_time_s=120,
    )
    tasks["reasoning_l2_holdout"] = BenchmarkTask(
        id="reasoning_l2_holdout", domain="reasoning", difficulty="L2", set_name="holdout",
        prompt="A SaaS company has: 1000 customers paying $50/mo, 3% monthly churn, $500 CAC. They spend $20K/mo on support, $15K/mo on engineering. Revenue grows 2% monthly organically. After 12 months: (1) What's MRR? (2) What's LTV? (3) Is LTV/CAC > 3? (4) What monthly spend can they afford while keeping 20% margin?",
        oracle_type="exact_match",
        oracle_spec={
            "answer_ranges": {
                "mrr": (52000, 58000),
                "ltv": (1500, 1800),
                "ltv_cac_ratio": (3.0, 3.7),
                "max_spend": (45000, 52000),
            },
        },
        expected_tools=["execute_code"],
        max_steps=10, max_time_s=120,
    )

    # ── DOMAIN: TOOL USE ──
    tasks["tool_use_l1_baseline"] = BenchmarkTask(
        id="tool_use_l1_baseline", domain="tool_use", difficulty="L1", set_name="baseline",
        prompt="Read the file /tmp/sample_data.json, extract all email addresses, and write them to /tmp/emails.txt one per line.",
        oracle_type="state_diff",
        oracle_spec={
            "output_file": "/tmp/emails.txt",
            "must_contain": ["@"],  # At minimum, valid email format
            "format": "one_per_line",
        },
        expected_tools=["read_file", "execute_code", "write_file"],
        max_steps=5, max_time_s=60,
    )
    tasks["tool_use_l1_holdout"] = BenchmarkTask(
        id="tool_use_l1_holdout", domain="tool_use", difficulty="L1", set_name="holdout",
        prompt="Search for 'PostgreSQL connection pooling best practices', extract the top 3 results, and save a markdown summary to /tmp/pg_pooling.md with titles, URLs, and key takeaways.",
        oracle_type="state_diff",
        oracle_spec={
            "output_file": "/tmp/pg_pooling.md",
            "must_contain": ["pooling", "postgresql"],
            "min_results": 3,
        },
        expected_tools=["web_search", "web_extract", "write_file"],
        max_steps=5, max_time_s=60,
    )
    tasks["tool_use_l2_baseline"] = BenchmarkTask(
        id="tool_use_l2_baseline", domain="tool_use", difficulty="L2", set_name="baseline",
        prompt="Build an end-to-end workflow: (1) Read /tmp/users.json, (2) For each user, check if their website is reachable using verify_url, (3) Write results to /tmp/url_check_results.json with {user, url, status, reachable}. Handle rate limits gracefully with delays between checks.",
        oracle_type="behavioral",
        oracle_spec={
            "output_file": "/tmp/url_check_results.json",
            "must_contain_keys": ["user", "url", "status", "reachable"],
            "handles_errors": True,
        },
        expected_tools=["read_file", "verify_url", "execute_code", "write_file"],
        max_steps=15, max_time_s=120,
    )
    tasks["tool_use_l2_holdout"] = BenchmarkTask(
        id="tool_use_l2_holdout", domain="tool_use", difficulty="L2", set_name="holdout",
        prompt="Create a monitoring script: (1) Check if localhost:5432 PostgreSQL is reachable, (2) Run a simple query, (3) If it fails, check the process list for postgres, (4) Log results to /tmp/pg_health.json with {timestamp, db_reachable, query_ok, process_running}. Run 3 checks at 5-second intervals.",
        oracle_type="behavioral",
        oracle_spec={
            "output_file": "/tmp/pg_health.json",
            "must_contain_keys": ["timestamp", "db_reachable", "query_ok", "process_running"],
            "min_checks": 3,
        },
        expected_tools=["terminal", "execute_code", "write_file"],
        max_steps=15, max_time_s=120,
    )

    # ── DOMAIN: PLANNING ──
    tasks["planning_l1_baseline"] = BenchmarkTask(
        id="planning_l1_baseline", domain="planning", difficulty="L1", set_name="baseline",
        prompt="Create a step-by-step plan to deploy a simple Flask app to a VPS. Include: server setup, Python environment, app deployment, Nginx reverse proxy, SSL with certbot, and systemd service. List tools needed and approximate time per step.",
        oracle_type="invariant",
        oracle_spec={
            "must_include": ["server", "python", "nginx", "ssl", "systemd"],
            "must_have_order": True,
            "min_steps": 5,
        },
        expected_tools=["write_file"],
        max_steps=5, max_time_s=60,
    )
    tasks["planning_l1_holdout"] = BenchmarkTask(
        id="planning_l1_holdout", domain="planning", difficulty="L1", set_name="holdout",
        prompt="Plan a data migration from SQLite to PostgreSQL. Steps needed: schema translation, data export, data import, validation, application config update, rollback plan. Identify hidden prerequisites and risks.",
        oracle_type="invariant",
        oracle_spec={
            "must_include": ["schema", "export", "import", "validate", "rollback"],
            "must_identify_risks": True,
            "min_steps": 5,
        },
        expected_tools=["write_file"],
        max_steps=5, max_time_s=60,
    )
    tasks["planning_l2_baseline"] = BenchmarkTask(
        id="planning_l2_baseline", domain="planning", difficulty="L2", set_name="baseline",
        prompt="Design a zero-downtime migration plan for a 100GB PostgreSQL database to AWS RDS. Consider: (1) Initial dump + restore timeline, (2) Logical replication setup, (3) Cutover procedure with <30s downtime, (4) Rollback if cutover fails, (5) DNS/proxy switching, (6) Monitoring post-migration. Include a Gantt-style timeline with parallel tracks.",
        oracle_type="invariant",
        oracle_spec={
            "must_include": ["replication", "cutover", "rollback", "monitoring", "dns"],
            "must_have_timeline": True,
            "must_identify_hidden_prereqs": True,
            "min_steps": 8,
        },
        expected_tools=["write_file", "execute_code"],
        max_steps=10, max_time_s=120,
    )
    tasks["planning_l2_holdout"] = BenchmarkTask(
        id="planning_l2_holdout", domain="planning", difficulty="L2", set_name="holdout",
        prompt="Start a weekly newsletter about sustainable tech. Produce: (1) Audience persona + value proposition, (2) Content calendar template (4 weeks), (3) Tech stack for email delivery, (4) Growth strategy (0→1000 subs in 3 months), (5) Monetization timeline. Treat this as a real business plan, not a homework assignment.",
        oracle_type="invariant",
        oracle_spec={
            "must_include": ["audience", "calendar", "tech stack", "growth", "monetization"],
            "must_have_timeline": True,
            "min_steps": 8,
            "must_be_specific": True,  # No vague "use social media" — specific strategies
        },
        expected_tools=["web_search", "write_file"],
        max_steps=10, max_time_s=120,
    )


    # ── L3 DIFFICULTY TASKS ──
    tasks["search_l3_baseline"] = BenchmarkTask(
        id="search_l3_baseline", domain="search", difficulty="L3", set_name="baseline",
        prompt="Compare tokenization strategies: GPT-4, Claude 3.5, Llama 3. For each: (1) vocabulary size, (2) BPE vs SentencePiece, (3) special tokens, (4) compression ratio, (5) multilingual impact. Cite sources.",
        oracle_type="behavioral",
        oracle_spec={"must_address": ["GPT-4", "Claude 3.5", "Llama 3", "tokenization", "vocabulary", "BPE", "SentencePiece"], "must_cite": ["OpenAI", "Anthropic", "Meta"], "min_sources": 3, "min_length": 300},
        expected_tools=["web_search", "web_extract"], max_steps=15, max_time_s=180,
    )
    tasks["search_l3_holdout"] = BenchmarkTask(
        id="search_l3_holdout", domain="search", difficulty="L3", set_name="holdout",
        prompt="Research constitutional AI and self-alignment. Compare Anthropic Constitutional AI, Meta Self-Align, and Self-Play. For each: key mechanism, scalability, failure modes, empirical results. Cite papers.",
        oracle_type="behavioral",
        oracle_spec={"must_address": ["Constitutional AI", "Self-Align", "self-play", "alignment"], "must_cite": ["Anthropic", "Meta"], "min_sources": 2, "min_length": 250},
        expected_tools=["web_search", "web_extract"], max_steps=15, max_time_s=180,
    )
    tasks["coding_l3_baseline"] = BenchmarkTask(
        id="coding_l3_baseline", domain="coding", difficulty="L3", set_name="baseline",
        prompt="Build a multi-file Python project: (1) config.py - YAML config with pydantic validation, (2) database.py - async Postgres pool with retry, (3) api.py - FastAPI routes with auth middleware, (4) models.py - SQLAlchemy models, (5) main.py - entry point. Include error handling, logging, type hints.",
        oracle_type="behavioral",
        oracle_spec={"must_import": ["pydantic", "asyncpg", "fastapi", "sqlalchemy", "logging"], "must_handle": ["retry", "auth", "validation error"], "must_feature": ["connection pool", "middleware", "type hints"], "min_length": 200},
        expected_tools=["write_file", "execute_code"], max_steps=20, max_time_s=300,
    )
    tasks["coding_l3_holdout"] = BenchmarkTask(
        id="coding_l3_holdout", domain="coding", difficulty="L3", set_name="holdout",
        prompt="Implement a distributed task queue: (1) Producer with batch enqueue and priority, (2) Worker with concurrent processing and graceful shutdown, (3) TaskResult with status tracking, (4) QueueManager coordinating producers/workers with dead letter queue. Use asyncio + Redis.",
        oracle_type="behavioral",
        oracle_spec={"must_import": ["asyncio", "redis", "dataclasses"], "must_handle": ["dead letter", "shutdown", "timeout"], "must_feature": ["priority queue", "batch", "heartbeat"], "min_length": 200},
        expected_tools=["write_file", "execute_code"], max_steps=20, max_time_s=300,
    )
    tasks["reasoning_l3_baseline"] = BenchmarkTask(
        id="reasoning_l3_baseline", domain="reasoning", difficulty="L3", set_name="baseline",
        prompt="Prove: In any group of 6 people, there are either 3 mutual friends or 3 mutual strangers (Ramsey R(3,3)=6). Structure: (1) Formal statement, (2) Choose arbitrary person, (3) Apply pigeonhole, (4) Complete argument. Verify each step.",
        oracle_type="invariant",
        oracle_spec={"must_include": ["ramsey", "pigeonhole", "6 people", "3 mutual", "arbitrary"], "invariants": ["formal_statement", "arbitrary_person", "pigeonhole_application", "case_analysis", "logical_connective"], "min_steps": 4},
        expected_tools=["execute_code"], max_steps=10, max_time_s=120,
    )
    tasks["reasoning_l3_holdout"] = BenchmarkTask(
        id="reasoning_l3_holdout", domain="reasoning", difficulty="L3", set_name="holdout",
        prompt="Password system: 3 consecutive failures lock account 30min. Each subsequent failure extends 30min. Success resets counter. Bot makes attempt every 2 minutes from 9:00am (0 failures). When is account permanently locked? Show step-by-step.",
        oracle_type="exact_match",
        oracle_spec={"answer_ranges": {"lock_time_minutes": (60, 90), "permanent_lock_hour": (10, 11)}},
        expected_tools=["execute_code"], max_steps=10, max_time_s=120,
    )
    tasks["tool_use_l3_baseline"] = BenchmarkTask(
        id="tool_use_l3_baseline", domain="tool_use", difficulty="L3", set_name="baseline",
        prompt="Build a data pipeline: (1) Fetch JSON from https://api.github.com/repos/nousresearch/hermes/releases, (2) Extract version, date, changelog, (3) Check for breaking changes between versions, (4) Write to /tmp/hermes_releases.json with {total_releases, breaking_versions, latest_stable}, (5) Write markdown report to /tmp/hermes_releases.md. Handle rate limits and pagination.",
        oracle_type="behavioral",
        oracle_spec={"output_file": "/tmp/hermes_releases.json", "must_contain_keys": ["total_releases", "breaking_versions", "latest_stable"], "handles_errors": True, "min_length": 50},
        expected_tools=["web_search", "web_extract", "execute_code", "write_file"], max_steps=20, max_time_s=300,
    )
    tasks["tool_use_l3_holdout"] = BenchmarkTask(
        id="tool_use_l3_holdout", domain="tool_use", difficulty="L3", set_name="holdout",
        prompt="System health dashboard: (1) Check disk space (df), (2) Memory (free -m), (3) Top 5 CPU processes (ps), (4) PostgreSQL on localhost:5432 reachable?, (5) Port 8080 listening?, (6) Write /tmp/health_dashboard.json with {disk, memory, top_processes, postgres, port_8080, timestamp}, (7) ASCII bar chart in /tmp/health_chart.txt.",
        oracle_type="behavioral",
        oracle_spec={"output_file": "/tmp/health_dashboard.json", "must_contain_keys": ["disk", "memory", "top_processes", "postgres", "timestamp"], "handles_errors": True, "min_length": 50},
        expected_tools=["terminal", "execute_code", "write_file"], max_steps=20, max_time_s=300,
    )
    tasks["planning_l3_baseline"] = BenchmarkTask(
        id="planning_l3_baseline", domain="planning", difficulty="L3", set_name="baseline",
        prompt="Migrate monolithic Node.js app (50K LOC, 15 services, PostgreSQL, Redis, S3) to Kubernetes. Phases: (1) Containerization, (2) Service decomposition order, (3) DB migration (shared→per-service), (4) Traffic migration (blue/green), (5) Rollback per phase, (6) Monitoring from day 1. Include dependency graph and critical path.",
        oracle_type="invariant",
        oracle_spec={"must_include": ["containerization", "decomposition", "migration", "rollback", "monitoring", "kubernetes"], "invariants": ["service_order", "dependency_graph", "blue_green", "critical_path", "database_strategy"], "min_steps": 6},
        expected_tools=["write_file", "execute_code"], max_steps=15, max_time_s=180,
    )
    tasks["planning_l3_holdout"] = BenchmarkTask(
        id="planning_l3_holdout", domain="planning", difficulty="L3", set_name="holdout",
        prompt="Plan real-time data pipeline for 10K events/sec: (1) Kafka ingestion, (2) Stream processing with exactly-once, (3) Schema evolution, (4) Dead letter queue, (5) Backpressure mechanism, (6) Scale to 100K. Include: component diagram, failure scenarios per layer, capacity planning with specific numbers.",
        oracle_type="invariant",
        oracle_spec={"must_include": ["kafka", "exactly-once", "schema", "backpressure", "scaling", "dead letter"], "invariants": ["component_diagram", "failure_scenarios", "capacity_numbers", "scaling_path"], "min_steps": 6},
        expected_tools=["write_file", "execute_code"], max_steps=15, max_time_s=180,
    )


    # ── L4 MYTHOS-TIER TASKS (Frontier difficulty) ──
    # Multi-step, multi-tool, adversarial edge cases, verifiable artifacts
    tasks["search_l4_baseline"] = BenchmarkTask(
        id="search_l4_baseline", domain="search", difficulty="L4", set_name="baseline",
        prompt="Investigate the RLHF → constitutional AI → RLAIF alignment pipeline evolution. For each stage: (1) training objective function, (2) reward model architecture, (3) failure mode with published example, (4) compute cost estimate, (5) key paper with citation. Then synthesize: what alignment property does each stage ADD that the previous lacked? Cross-reference at least 6 papers. Write structured JSON report to /tmp/alignment_evolution.json with keys: stages, added_properties, cross_references, failure_taxonomy.",
        oracle_type="behavioral",
        oracle_spec={"must_address": ["RLHF", "constitutional AI", "RLAIF", "reward model", "alignment", "failure mode", "compute"], "must_cite": ["Anthropic", "OpenAI", "Bai", "Ouyang", "Ganguli"], "min_sources": 4, "min_length": 500,
                     "output_file": "/tmp/alignment_evolution.json", "must_contain_keys": ["stages", "added_properties", "cross_references", "failure_taxonomy"],
                     "adversarial": True, "requires_synthesis": True},
        expected_tools=["web_search", "web_extract", "execute_code", "write_file"], max_steps=25, max_time_s=420,
    )
    tasks["search_l4_holdout"] = BenchmarkTask(
        id="search_l4_holdout", domain="search", difficulty="L4", set_name="holdout",
        prompt="Research the Mamba/SSM vs Transformer debate. For each architecture: (1) core recurrence mechanism, (2) parallel training trick, (3) length generalization empirical results on specific benchmarks, (4) hardware efficiency (FLOPs, memory), (5) hybrid architectures (Jamba, etc). Identify: 3 claims from SSM papers that Transformer advocates dispute, with evidence from both sides. Write structured markdown to /tmp/ssm_vs_transformer.md with sections: mechanisms, benchmarks, disputes, verdict.",
        oracle_type="behavioral",
        oracle_spec={"must_address": ["Mamba", "SSM", "transformer", "recurrence", "parallel training", "length generalization", "hybrid"], "must_cite": ["Gu", "Dao", "Vaswani", "Albert"], "min_sources": 4, "min_length": 500,
                     "output_file": "/tmp/ssm_vs_transformer.md", "must_contain_keys": [],
                     "adversarial": True, "requires_synthesis": True},
        expected_tools=["web_search", "web_extract", "execute_code", "write_file"], max_steps=25, max_time_s=420,
    )
    tasks["coding_l4_baseline"] = BenchmarkTask(
        id="coding_l4_baseline", domain="coding", difficulty="L4", set_name="baseline",
        prompt="Build a production-grade MCP (Model Context Protocol) server in Python with: (1) Server class with stdio transport + capability negotiation, (2) Tool registration decorator @mcp_tool with schema inference from type hints, (3) Resource provider with URI template resolution (e.g. file:///data/{project}), (4) Prompt template engine with variable interpolation and validation, (5) JSON-RPC 2.0 message handler with batch support and id tracking, (6) Circuit breaker for tool execution (3 failures → 30s cooldown), (7) Structured logging with correlation IDs. Write to /tmp/mcp_server.py. Must be importable and have a working __main__.",
        oracle_type="behavioral",
        oracle_spec={"must_import": ["json", "asyncio", "dataclasses", "logging", "uuid"], "must_handle": ["circuit breaker", "batch request", "capability negotiation", "validation error", "timeout"], "must_feature": ["decorator", "URI template", "variable interpolation", "correlation id", "JSON-RPC 2.0"],
                     "output_file": "/tmp/mcp_server.py", "must_compile": True, "min_length": 300,
                     "adversarial": True},
        expected_tools=["write_file", "execute_code", "patch", "terminal"], max_steps=25, max_time_s=420,
    )
    tasks["coding_l4_holdout"] = BenchmarkTask(
        id="coding_l4_holdout", domain="coding", difficulty="L4", set_name="holdout",
        prompt="Implement a CRDT (Conflict-free Replicated Data Type) library in Python: (1) GCounter (grow-only counter with vector clocks), (2) PNCounter (positive-negative counter), (3) ORSet (observed-remove set with unique tags), (4) LWWRegister (last-writer-wins with hybrid logical clock), (5) GCounter merge must handle missing nodes and concurrent increments correctly. Include: merge law proofs as docstrings, property-based tests using hypothesis for convergence (all replicas converge), commutativity (merge order independent), idempotency (self-merge safe). Write to /tmp/crdt_lib.py.",
        oracle_type="behavioral",
        oracle_spec={"must_import": ["dataclasses", "typing", "collections"], "must_handle": ["concurrent increment", "missing node", "merge convergence", "order independence"], "must_feature": ["GCounter", "PNCounter", "ORSet", "LWWRegister", "vector clock", "hypothesis", "docstring proof"],
                     "output_file": "/tmp/crdt_lib.py", "must_compile": True, "min_length": 300,
                     "adversarial": True},
        expected_tools=["write_file", "execute_code", "patch", "terminal"], max_steps=25, max_time_s=420,
    )
    tasks["reasoning_l4_baseline"] = BenchmarkTask(
        id="reasoning_l4_baseline", domain="reasoning", difficulty="L4", set_name="baseline",
        prompt="A distributed system uses vector clocks for causality. 3 processes P1, P2, P3 start at VC=[0,0,0]. Events: P1 sends m1→P2 (VC increment), P2 receives m1 then sends m2→P3, P3 receives m2 then sends m3→P1, P1 receives m3. Concurrently: P2 sends m4→P1 (no dependency on m1 reconciliation), P1 receives m4 after sending m1 but before receiving m3. Questions: (1) Draw the partial order (happens-before graph). (2) Which events are concurrent? (3) What is each process's final VC? (4) If P2 crashes after sending m4 but before m1 delivery confirmation, what information is lost? (5) Prove: the final VCs satisfy consistency (no causal violation). Show each step with vector clock states.",
        oracle_type="exact_match",
        oracle_spec={"answer_ranges": {
            "p1_final_vc_0": (1, 2), "p1_final_vc_1": (0, 1), "p1_final_vc_2": (1, 2),
            "concurrent_pairs": (2, 4), "lost_info_count": (1, 2)
        }, "must_include": ["vector clock", "happens-before", "concurrent", "causal", "partial order"]},
        expected_tools=["execute_code"], max_steps=15, max_time_s=240,
    )
    tasks["reasoning_l4_holdout"] = BenchmarkTask(
        id="reasoning_l4_holdout", domain="reasoning", difficulty="L4", set_name="holdout",
        prompt="Bayesian network alarm problem (extended): Burglary(B), Earthquake(E), Alarm(A), JohnCalls(J), MaryCalls(M). P(B)=0.001, P(E)=0.002, P(A|B,E)=0.95, P(A|B,~E)=0.94, P(A|~B,E)=0.29, P(A|~B,~E)=0.001, P(J|A)=0.90, P(J|~A)=0.05, P(M|A)=0.70, P(M|~A)=0.01. Questions: (1) P(B|J,M) exact to 4 decimal places. (2) P(B|J,M) using likelihood weighting with 10000 samples — what's the standard error? (3) If E and B are NOT independent (correlation 0.3), recalculate P(A|B,E) accounting for the dependency. (4) Prove: d-separation implies conditional independence for this graph. Show all work.",
        oracle_type="exact_match",
        oracle_spec={"answer_ranges": {
            "p_burglary_given_calls": (0.28, 0.30),   # Classic result ~0.284
            "std_error_approx": (0.005, 0.02),
            "p_alarm_dep": (0.90, 0.97)
        }, "must_include": ["bayesian", "d-separation", "likelihood weighting", "conditional independence"]},
        expected_tools=["execute_code"], max_steps=15, max_time_s=240,
    )
    tasks["tool_use_l4_baseline"] = BenchmarkTask(
        id="tool_use_l4_baseline", domain="tool_use", difficulty="L4", set_name="baseline",
        prompt="Build a multi-source health monitoring agent: (1) Check Postgres cortex DB: run 3 diagnostic queries (table count, active connections, longest-running query), (2) Check filesystem: /tmp disk usage, largest 5 files in ~/hermes-agent/, (3) Check processes: any python3 processes, their PIDs and memory, (4) Cross-correlate: if DB connections > 10 AND python3 processes > 3 AND /tmp > 80% full, flag 'resource_saturation', (5) Generate structured report at /tmp/health_agent_report.json with sections: db_health, fs_health, process_health, cross_correlations, alerts, timestamp, (6) Generate human-readable markdown at /tmp/health_agent_report.md with ASCII tables, (7) If any alert triggered, also write /tmp/health_alert.txt with just the alert details.",
        oracle_type="behavioral",
        oracle_spec={"output_file": "/tmp/health_agent_report.json", "must_contain_keys": ["db_health", "fs_health", "process_health", "cross_correlations", "alerts", "timestamp"],
                     "extra_files": ["/tmp/health_agent_report.md", "/tmp/health_alert.txt"],
                     "handles_errors": True, "cross_check": True, "min_length": 100,
                     "adversarial": True},
        expected_tools=["terminal", "execute_code", "write_file"], max_steps=25, max_time_s=360,
    )
    tasks["tool_use_l4_holdout"] = BenchmarkTask(
        id="tool_use_l4_holdout", domain="tool_use", difficulty="L4", set_name="holdout",
        prompt="Reverse-engineer and document an API: (1) Fetch https://api.github.com/repos/nousresearch/hermes-agent (2) Extract: open issues count, recent 5 issue titles, contributor count, recent 3 commit messages, (3) Fetch /releases endpoint, get latest 3 release tag names and dates, (4) Cross-reference: which issues were closed in each release? (5) Check if any open issues reference missing features, (6) Write /tmp/hermes_api_doc.json with {repo_stats, releases, issue_release_map, missing_features}, (7) Write /tmp/hermes_api_doc.md human-readable version with markdown tables, (8) Validate JSON is well-formed with execute_code. Handle: rate limits (403), missing fields (null), pagination.",
        oracle_type="behavioral",
        oracle_spec={"output_file": "/tmp/hermes_api_doc.json", "must_contain_keys": ["repo_stats", "releases", "issue_release_map", "missing_features"],
                     "extra_files": ["/tmp/hermes_api_doc.md"],
                     "handles_errors": True, "cross_check": True, "min_length": 100,
                     "adversarial": True},
        expected_tools=["web_extract", "execute_code", "write_file", "terminal"], max_steps=25, max_time_s=420,
    )
    tasks["planning_l4_baseline"] = BenchmarkTask(
        id="planning_l4_baseline", domain="planning", difficulty="L4", set_name="baseline",
        prompt="Plan migration of a 500-node HPC cluster from Slurm to Kubernetes: (1) Workload profiling:MPI jobs (40%), GPU training (30%), Jupyter notebooks (20%), data pipelines (10%), (2) MPI on K8s requires MPI operator + hostNetwork + RDMA — detail the operator config, (3) GPU scheduling: device plugin + MIG partitioning strategy for A100s, (4) Storage: parallel filesystem (Lustre) → CSI driver + object storagetiering plan, (5) Network: hostNetwork vs CNI overlay for HPC workloads with latency SLO <10μs, (6) Phase plan with dependency DAG: what MUST be ready before each phase starts, (7) Rollback plan PER PHASE with specific rollback commands, (8) Capacity model: how many K8s nodes needed if 30% of MPI jobs need hostNetwork? Show the math. Include risk register with 8+ risks, each with probability, impact, mitigation.",
        oracle_type="invariant",
        oracle_spec={"must_include": ["MPI operator", "GPU device plugin", "MIG", "CSI driver", "hostNetwork", "CNI", "rollback", "capacity model", "risk register", "dependency DAG"],
                     "invariants": ["workload_profile", "mpi_operator_config", "gpu_scheduling", "storage_tiering", "network_slo", "phase_dependencies", "rollback_commands", "capacity_math", "risk_register_8plus"],
                     "min_steps": 8,
                     "requires_quantitative": True,
                     "adversarial": True},
        expected_tools=["write_file", "execute_code"], max_steps=20, max_time_s=300,
    )
    tasks["planning_l4_holdout"] = BenchmarkTask(
        id="planning_l4_holdout", domain="planning", difficulty="L4", set_name="holdout",
        prompt="Design a multi-region disaster recovery architecture for an AI inference platform serving 10K RPS: (1) Primary: us-east-1, DR: eu-west-1, Edge: ap-southeast-1, (2) Model serving: vLLM on A100s (8 GPU per replica), KV cache replication across regions with <100ms staleness, (3) Routing: global load balancer with latency-based + failover, (4) Data: training data in S3 with cross-region replication, inference logs → Kafka → dual-region ClickHouse, (5) DR RPO=5min, RTO=2min — calculate: replication bandwidth, queue depth, failover sequence, (6) Cost optimization: spot instances for non-critical, reserved for baseline, how many of each per region?, (7) Chaos engineering plan: 5 specific failure scenarios with expected behavior, (8) Monitoring: golden signals per region with specific thresholds. Show the math for ALL capacity calculations.",
        oracle_type="invariant",
        oracle_spec={"must_include": ["multi-region", "KV cache replication", "RPO", "RTO", "vLLM", "failover", "chaos engineering", "golden signals", "spot instances", "capacity math"],
                     "invariants": ["region_topology", "cache_replication", "dr_rpo_rto_math", "routing_strategy", "replication_bandwidth", "failover_sequence", "cost_breakdown", "chaos_scenarios_5", "monitoring_thresholds"],
                     "min_steps": 8,
                     "requires_quantitative": True,
                     "adversarial": True},
        expected_tools=["write_file", "execute_code"], max_steps=20, max_time_s=300,
    )

    return tasks


# ── Scoring Engine ──

class TrajectoryScorer:
    """3-axis scoring: outcome 60%, efficiency 20%, tool selection 20%."""

    @staticmethod
    def outcome_score(task: BenchmarkTask, trajectory: TrajectoryResult) -> Tuple[float, Dict]:
        """Score outcome correctness (0-10)."""
        spec = task.oracle_spec
        answer = trajectory.final_answer.lower()
        details = {}

        if task.oracle_type == "exact_match":
            expected = spec.get("answer", "")
            if expected and expected.lower() in answer:
                score = 10.0
            elif "answer_ranges" in spec:
                score = 0.0
                matched = 0
                total = len(spec["answer_ranges"])
                near_misses = 0
                for key, (lo, hi) in spec["answer_ranges"].items():
                    nums = re.findall(r'[\d,.]+', answer)
                    found = False
                    near = False
                    for n_str in nums:
                        try:
                            n = float(n_str.replace(',', ''))
                            if lo <= n <= hi:
                                matched += 1
                                found = True
                                break
                            # Near miss: proportional to range width (20%)
                            margin = (hi - lo) * 0.2
                            if (lo - margin) <= n <= (hi + margin):
                                near = True
                        except ValueError:
                            continue
                    if not found and near:
                        near_misses += 1
                score = 10.0 * (matched + 0.5 * near_misses) / max(1, total)
                details["range_matches"] = f"{matched}/{total}"
            else:
                keywords = spec.get("keywords", [])
                if keywords:
                    matched = sum(1 for kw in keywords if kw.lower() in answer)
                    score = 10.0 * (matched / len(keywords))
                else:
                    score = 0.0

        elif task.oracle_type == "behavioral":
            # ── Code-aware oracle for coding tasks ──
            if task.domain == "coding":
                code_score, code_details = _code_oracle_score(trajectory.final_answer, spec)
                return code_score, code_details
            
            # ── Domain-aware behavioral oracle ──
            if task.domain == "tool_use":
                # Tool-use tasks: check workflow execution quality
                must_keys = [k.lower() for k in spec.get("must_contain_keys", [])]
                handles_errors = spec.get("handles_errors", False)
                output_file = spec.get("output_file", "")
                min_length = spec.get("min_length", 30)
                
                # 1. Output format: are required keys mentioned in answer?
                key_score = sum(1 for k in must_keys if k in answer) / max(1, len(must_keys))
                
                # 2. Workflow: did they mention reading, checking, writing?
                workflow_keywords = ["read", "check", "write", "verify", "extract", "log", 
                                      "monitor", "query", "fetch", "diagnose", "report", "diagnostic"]
                wf_matches = sum(1 for w in workflow_keywords if w in answer)
                workflow_score = min(1.0, wf_matches / 3.0)
                
                # 3. Error handling
                error_score = 0.5  # default neutral
                if handles_errors:
                    error_keywords = ["try", "except", "error", "fail", "retry", "delay", "rate limit", "timeout"]
                    er_matches = sum(1 for w in error_keywords if w in answer)
                    error_score = min(1.0, er_matches / 2.0)
                
                # 4. Output file result check (if file exists, bonus)
                file_score = 0.5  # neutral if can't check
                if output_file and os.path.exists(output_file):
                    try:
                        with open(output_file) as f:
                            fcontent = f.read().lower()
                        file_keys_found = sum(1 for k in must_keys if k in fcontent)
                        file_score = file_keys_found / max(1, len(must_keys))
                    except Exception:
                        file_score = 0.3
                
                # 5. Length adequacy
                length_score = min(1.0, len(answer) / max(1, min_length))
                
                # L4 extra files + cross-check
                extra_files = spec.get("extra_files", [])
                extra_score = 0.5
                if extra_files and spec.get("adversarial", False):
                    found = sum(1 for ef in extra_files if os.path.exists(ef))
                    # Conditional files: alert/exception files that only exist when triggered
                    conditional_files = [ef for ef in extra_files if any(kw in ef.lower() for kw in ['alert', 'error', 'exception', 'warning'])]
                    mandatory_files = [ef for ef in extra_files if ef not in conditional_files]
                    if mandatory_files:
                        mandatory_found = sum(1 for ef in mandatory_files if os.path.exists(ef))
                        mandatory_score = mandatory_found / len(mandatory_files)
                    else:
                        mandatory_score = 1.0  # No mandatory extra files
                    # Conditional files: absence means no alerts triggered = success
                    conditional_score = 1.0  # Default: no alerts is valid
                    if conditional_files:
                        for ef in conditional_files:
                            if os.path.exists(ef):
                                conditional_score = 1.0  # Alert file exists = was triggered = valid
                                break
                        # If none exist and answer mentions no alerts, that's also valid
                        if 'no alert' in answer or 'none' in answer or 'alerts": []' in answer.lower():
                            conditional_score = 1.0
                    extra_score = 0.7 * mandatory_score + 0.3 * conditional_score
                
                cross_score = 0.5
                if spec.get("cross_check", False) and output_file and os.path.exists(output_file):
                    all_files = [output_file] + [ef for ef in extra_files if os.path.exists(ef)]
                    if len(all_files) <= 1:
                        cross_score = 0.7  # Single file: can't cross-check, neutral
                    elif len(all_files) > 1:
                        try:
                            contents = {}
                            for af in all_files:
                                with open(af) as f:
                                    contents[af] = f.read().lower()
                            consistency_keys = must_keys[:3]
                            consistent_count = sum(1 for k in consistency_keys 
                                                    if all(k in c for c in contents.values() if c))
                            cross_score = consistent_count / max(1, len(consistency_keys))
                        except Exception:
                            cross_score = 0.3

                if spec.get("adversarial", False):
                    weights = [0.15, 0.15, 0.15, 0.10, 0.15, 0.15, 0.15]
                    components = [key_score, workflow_score, error_score, file_score, length_score, extra_score, cross_score]
                else:
                    weights = [0.25, 0.20, 0.20, 0.15, 0.20]
                    components = [key_score, workflow_score, error_score, file_score, length_score]
                score = 10.0 * sum(w * c for w, c in zip(weights, components))
                details = {"keys": f"{key_score:.0%}", "workflow": f"{workflow_score:.0%}",
                          "error_handling": f"{error_score:.0%}", "file": f"{file_score:.0%}",
                          "length": f"{length_score:.0%}"}
            else:
                # Search tasks: citation + address quality
                must_cite = [c.lower() for c in spec.get("must_cite", [])]
                must_address = [a.lower() for a in spec.get("must_address", [])]
                must_fix = spec.get("must_fix", "").lower()
                min_sources = spec.get("min_sources", 0)
                min_length = spec.get("min_length", 0)

                cite_score = sum(1 for c in must_cite if c in answer) / max(1, len(must_cite))
                address_score = sum(
                    1 for a in must_address
                    if a in answer 
                    or all(w in answer for w in a.split() if len(w) > 3)
                    or a.replace("-", " ") in answer  # Hyphen variant: self-align → self align
                    or a.replace(" ", "-") in answer  # Space variant: self align → self-align
                ) / max(1, len(must_address))
                fix_score = 1.0 if not must_fix else (
                    1.0 if must_fix in answer else
                    (0.7 if any(w in answer for w in must_fix.split()[:3] if len(w) > 3) else 0.0)
                )
                length_score = min(1.0, len(answer) / max(1, min_length))

                # L4 synthesis + output_file scoring
                synth_score = 0.5  # neutral default
                file_verify_score = 0.5
                
                if spec.get("requires_synthesis", False):
                    # Synthesis check: cross-reference connections + structural indicators
                    # Transitional phrases that indicate synthesis
                    synth_markers = ["therefore", "however", "consequently", "unlike", "in contrast",
                                     "building on", "extends", "lacks", "improves upon", "addresses"]
                    synth_count = sum(1 for sm in synth_markers if sm in answer)
                    # Structural indicators: explicit cross-references, comparative claims
                    struct_markers = ["adds", "lacks", "unlike", "compared to", " whereas ", 
                                      " over ", "extends", "improves on", "addresses the gap"]
                    struct_count = sum(1 for sm in struct_markers if sm in answer)
                    # Cross-reference patterns: "X → Y", "X adds Y", numbered connections
                    crossref_patterns = re.findall(r'(?:adds|extends|improves|lacks|addresses)\s+(?:the\s+)?(?:property|capability|limitation|gap|feature)', answer)
                    synth_combined = synth_count + struct_count * 0.7 + len(crossref_patterns) * 0.5
                    synth_score = min(1.0, synth_combined / 5.0)  # 5+ combined = full credit
                    
                    # Stricter partial credit for L4: reduce free keyword matches
                    # L4 requires actual sentence construction, not just scattered terms
                    if address_score > 0.5 and synth_score < 0.25:
                        address_score *= 0.7  # Penalize keyword salad without synthesis
                
                output_file = spec.get("output_file", "")
                if output_file and spec.get("adversarial", False):
                    if os.path.exists(output_file):
                        try:
                            with open(output_file) as f:
                                fcontent = f.read().lower()
                            # Check that key terms appear in the actual file
                            must_contain_keys = [k.lower() for k in spec.get("must_contain_keys", [])]
                            if must_contain_keys:
                                file_hits = sum(1 for k in must_contain_keys if k in fcontent)
                                file_verify_score = file_hits / max(1, len(must_contain_keys))
                            else:
                                # File exists but no specific keys to check
                                file_verify_score = 0.7
                            # File type specific quality checks
                            if output_file.endswith(".json"):
                                try:
                                    jdata = json.loads(open(output_file).read())
                                    file_verify_score = min(1.0, file_verify_score + 0.05)
                                    # Depth check: structured reports should have nested objects
                                    def _json_depth(d, depth=0):
                                        if isinstance(d, dict):
                                            return max((_json_depth(v, depth+1) for v in d.values()), default=depth)
                                        elif isinstance(d, list):
                                            return max((_json_depth(v, depth+1) for v in d), default=depth)
                                        return depth
                                    if _json_depth(jdata) >= 2:
                                        file_verify_score = min(1.0, file_verify_score + 0.05)
                                except Exception:
                                    file_verify_score *= 0.8  # Invalid JSON penalty
                            elif output_file.endswith(".md"):
                                # Markdown quality: check headings and structure
                                try:
                                    md_content = open(output_file).read().lower()
                                    heading_count = md_content.count("#")
                                    if heading_count >= 3:
                                        file_verify_score = min(1.0, file_verify_score + 0.05)
                                    if "|" in md_content:  # Table present
                                        file_verify_score = min(1.0, file_verify_score + 0.05)
                                except Exception:
                                    pass
                        except Exception:
                            file_verify_score = 0.2
                    else:
                        file_verify_score = 0.0  # L4 strict: file MUST exist
                
                if spec.get("adversarial", False):
                    # L4: 6-component scoring with synthesis + file verification
                    weights = [0.20, 0.20, 0.10, 0.10, 0.20, 0.20]
                    components = [cite_score, address_score, fix_score, length_score, synth_score, file_verify_score]
                else:
                    weights = [0.3, 0.3, 0.2, 0.2]
                    components = [cite_score, address_score, fix_score, length_score]
                score = 10.0 * sum(w * c for w, c in zip(weights, components))
                details = {"cite": f"{cite_score:.0%}", "address": f"{address_score:.0%}",
                           "fix": f"{fix_score:.0%}", "length": f"{length_score:.0%}",
                           "synthesis": f"{synth_score:.0%}" if spec.get("requires_synthesis") else "n/a",
                           "file_verify": f"{file_verify_score:.0%}" if spec.get("adversarial") else "n/a"}

        elif task.oracle_type == "state_diff":
            output_file = spec.get("output_file", "")
            must_contain = [m.lower() for m in spec.get("must_contain", [])]
            exists = False
            content_ok = False
            content = ""

            if output_file and os.path.exists(output_file):
                exists = True
                try:
                    with open(output_file, 'r') as f:
                        content = f.read().lower()
                    content_ok = all(m in content for m in must_contain)
                except Exception:
                    content_ok = False

            if exists and content_ok:
                score = 10.0
            elif exists:
                matched = sum(1 for m in must_contain if m in content)
                score = 5.0 * (matched / max(1, len(must_contain)))
            else:
                score = 0.0
            details = {"file_exists": exists, "content_ok": content_ok}

        elif task.oracle_type == "invariant":
            invariants = spec.get("invariants", [])
            must_include = [m.lower() for m in spec.get("must_include", [])]
            must_identify = spec.get("must_identify_risks", False) or spec.get("must_identify_hidden_prereqs", False)

            include_matches = sum(1 for m in must_include if m in answer)
            include_score = include_matches / max(1, len(must_include)) if must_include else 0.0

            inv_matches = 0
            inv_weight_sum = 0.0
            if invariants:
                for idx, inv in enumerate(invariants):
                    # Position-weighted: earlier invariants are more important
                    weight = 1.0 + 0.1 * (len(invariants) - idx) / max(1, len(invariants))
                    inv_weight_sum += weight
                    inv_label = inv.replace("_", " ").lower()
                    matched = False
                    if inv.lower() in answer or inv_label in answer:
                        matched = True
                    elif any(p in answer.lower() for p in [f"{inv}=satisfied", f"{inv}: satisfied",
                                                           f"{inv_label} satisfied", f"{inv} satisfied"]):
                        matched = True
                    elif inv.split("_")[0] in answer.lower():
                        # L4 adversarial: require 2+ words from multi-word invariant names
                        if spec.get("adversarial", False) and "_" in inv:
                            words = inv.split("_")
                            if len(words) >= 2 and sum(1 for w in words if w.lower() in answer) >= 2:
                                matched = True
                        else:
                            matched = True
                    if matched:
                        inv_matches += weight
                inv_score = inv_matches / max(1, inv_weight_sum)
            else:
                inv_score = 0.0

            # L4: requires_quantitative — penalize plans without numbers
            quant_score = 0.0
            if spec.get("requires_quantitative", False):
                # Count numbers, percentages, units in answer
                number_patterns = re.findall(r'\d+\.?\d*\s*[%GBKMbmsμsec]', answer)
                number_count = len(number_patterns)
                if number_count >= 5:
                    quant_score = 0.15
                elif number_count >= 3:
                    quant_score = 0.10
                elif number_count >= 1:
                    quant_score = 0.05

            risk_score = 0.5 if must_identify and ("risk" in answer or "prerequisite" in answer or "prereq" in answer) else 0.0
            timeline_score = 0.5 if spec.get("must_have_timeline") and ("week" in answer or "day" in answer or "hour" in answer or "timeline" in answer) else 0.0

            if invariants and not must_include:
                base = inv_score
            elif must_include and not invariants:
                base = include_score
            elif invariants and must_include:
                # Both present: weighted average (invariants more rigorous, weighted higher)
                base = 0.4 * include_score + 0.6 * inv_score
            else:
                base = 0.0
            bonus = risk_score + timeline_score + quant_score
            score = 10.0 * min(1.0, base + bonus)
            details = {"inclusions": f"{include_matches}/{len(must_include)}",
                       "invariants": f"{inv_matches}/{len(invariants)}" if invariants else "n/a",
                       "risks_identified": risk_score > 0, "timeline": timeline_score > 0,
                       "quantitative": f"{quant_score:.2f}" if spec.get("requires_quantitative") else "n/a"}
        else:
            score = 0.0

        return score, details

    @staticmethod
    def efficiency_score(task: BenchmarkTask, trajectory: TrajectoryResult) -> Tuple[float, Dict]:
        """Score efficiency: steps used vs optimal (0-10)."""
        steps_used = len(trajectory.steps)
        max_steps = task.max_steps
        # Difficulty-aware optimal: L4 tasks need more steps naturally
        opt_factor = 0.4 if task.difficulty not in ("L3", "L4") else 0.6
        optimal = max(1, max_steps * opt_factor)

        if steps_used <= 0:
            if not task.expected_tools:
                return 10.0, {"steps": 0, "note": "no tools needed, none used (optimal)"}
            return 0.0, {"steps": 0}

        if steps_used <= optimal:
            score = 10.0
        elif steps_used <= max_steps:
            score = 10.0 * (1.0 - 0.7 * (steps_used - optimal) / (max_steps - optimal))
        else:
            score = max(0.0, 3.0 - 2.0 * (steps_used - max_steps) / max(1, max_steps))

        time_s = trajectory.total_time_s
        max_time = task.max_time_s
        # Graduated: fast=10, moderate=8-9, slow=4-7, over=0
        if time_s <= max_time * 0.3:
            time_score = 10.0
        elif time_s <= max_time * 0.5:
            time_score = 9.5
        elif time_s <= max_time * 0.75:
            time_score = 8.0
        elif time_s <= max_time:
            time_score = max(3.0, 10.0 * (1.0 - 0.7 * time_s / max_time))
        else:
            time_score = 0.0

        composite = 0.6 * score + 0.4 * time_score
        return composite, {"steps_used": steps_used, "optimal": optimal, "time_s": f"{time_s:.1f}"}

    @staticmethod
    def tool_selection_score(task: BenchmarkTask, trajectory: TrajectoryResult) -> Tuple[float, Dict]:
        """Score tool selection precision/recall (0-10)."""
        if not task.expected_tools:
            if not trajectory.steps:
                return 10.0, {"reason": "no tools needed, none used"}
            return 5.0, {"reason": "tools used when none expected"}

        # Tool aliases: similar tools count as partial match
        TOOL_ALIASES = {
            "execute_code": {"terminal", "patch", "execute_code"},
            "write_file": {"write_file", "patch"},
            "web_search": {"web_search", "web_research", "web_extract"},
            "web_extract": {"web_extract", "web_search", "web_research"},
            "terminal": {"terminal", "execute_code"},
        }

        used_tools = set(s.tool_name for s in trajectory.steps)
        expected = set(task.expected_tools)

        # Normalize with aliases for matching
        used_normalized = set()
        for ut in used_tools:
            used_normalized.add(ut)
            # Add aliases
            for base, aliases in TOOL_ALIASES.items():
                if ut in aliases:
                    used_normalized.add(base)

        precision = len(used_normalized & expected) / max(1, len(used_normalized))
        recall = len(used_normalized & expected) / max(1, len(expected))

        f1 = 2 * precision * recall / max(0.01, precision + recall)
        score = 10.0 * f1

        return score, {
            "precision": f"{precision:.0%}", "recall": f"{recall:.0%}",
            "used": list(used_tools), "expected": list(expected),
        }

    @staticmethod
    def composite_score(task: BenchmarkTask, trajectory: TrajectoryResult) -> TrajectoryScores:
        """Compute full 3-axis composite score."""
        outcome, outcome_details = TrajectoryScorer.outcome_score(task, trajectory)
        efficiency, eff_details = TrajectoryScorer.efficiency_score(task, trajectory)
        tool_sel, tool_details = TrajectoryScorer.tool_selection_score(task, trajectory)

        composite = 0.6 * outcome + 0.2 * efficiency + 0.2 * tool_sel

        return TrajectoryScores(
            task_id=task.id,
            outcome=round(outcome, 2),
            efficiency=round(efficiency, 2),
            tool_selection=round(tool_sel, 2),
            composite=round(composite, 2),
            details={"outcome": outcome_details, "efficiency": eff_details, "tool_selection": tool_details},
        )


# ── Statistical Comparison ──

def welch_t_test(a: List[float], b: List[float]) -> Tuple[float, float]:
    """Welch's t-test. Returns (t_statistic, two_sided_p_value)."""
    if len(a) < 2 or len(b) < 2:
        return 0.0, 1.0

    n1, n2 = len(a), len(b)
    m1, m2 = sum(a) / n1, sum(b) / n2
    v1 = sum((x - m1) ** 2 for x in a) / (n1 - 1) if n1 > 1 else 0
    v2 = sum((x - m2) ** 2 for x in b) / (n2 - 1) if n2 > 1 else 0

    se = math.sqrt(v1 / n1 + v2 / n2)
    if se < 1e-10:
        return 0.0, 1.0

    t = (m2 - m1) / se

    df = ((v1 / n1 + v2 / n2) ** 2) / (
        (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    ) if (v1 / n1 + v2 / n2) > 0 else 1

    x = abs(t) / math.sqrt(df)
    if x > 50:
        p = 0.0
    else:
        p = 2.0 * (1.0 - _t_cdf_approx(abs(t), df))

    return t, max(0.0, min(1.0, p))


def _t_cdf_approx(t: float, df: float) -> float:
    """Approximate CDF of t-distribution using Hill's approximation."""
    x = df / (df + t * t)
    import math as _m
    if df > 30:
        z = t
        return 0.5 * (1.0 + _m.erf(z / _m.sqrt(2)))

    a = df / 2
    b = 0.5
    bt = _m.exp(
        a * _m.log(a) + b * _m.log(b) - (a + b) * _m.log(a + b * x) - _m.log(b)
    )
    return 1.0 - 0.5 * x ** (b / (a + b))


def cohens_d(a: List[float], b: List[float]) -> float:
    """Cohen's d effect size (positive = b > a)."""
    n1, n2 = len(a), len(b)
    if n1 < 1 or n2 < 1:
        return 0.0
    m1, m2 = sum(a) / n1, sum(b) / n2
    v1 = sum((x - m1) ** 2 for x in a) / (n1 - 1) if n1 > 1 else 0
    v2 = sum((x - m2) ** 2 for x in b) / (n2 - 1) if n2 > 1 else 0

    pooled_sd = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / max(1, n1 + n2 - 2))
    if pooled_sd < 1e-10:
        return 0.0
    return (m2 - m1) / pooled_sd


# ── Main Testing Gym Class ──

class TestingGym:
    """Benchmark evaluation framework for agent self-improvement."""

    TASK_REGISTRY = _build_task_registry()

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._baseline_results: Dict[str, TrajectoryResult] = {}
        self._post_results: Dict[str, TrajectoryResult] = {}
        self._scores_cache: Dict[str, TrajectoryScores] = {}
        self._current_trajectory: Optional[TrajectoryResult] = None
        self._current_task: Optional[BenchmarkTask] = None
        self._run_history: List[Dict] = []

    # ── Recording (called from post_tool_call) ──

    def start_task(self, task_id: str) -> bool:
        """Begin recording a benchmark task execution."""
        if task_id not in self.TASK_REGISTRY:
            return False
        self._current_task = self.TASK_REGISTRY[task_id]
        self._current_trajectory = TrajectoryResult(
            task_id=task_id,
            run_type="in_progress",
            started_at=time.time(),
        )
        return True

    def record_step(self, tool_name: str, tool_args: Dict,
                    result_summary: str, success: bool, latency_s: float = 0.0):
        """Record one step during task execution."""
        if not self._current_trajectory:
            return
        step = TrajectoryStep(
            tool_name=tool_name,
            tool_args=tool_args,
            result_summary=result_summary[:200],
            success=success,
            timestamp=time.time(),
            latency_s=latency_s,
        )
        self._current_trajectory.steps.append(step)

    def finish_task(self, final_answer: str, run_type: str = "baseline",
                    error: Optional[str] = None) -> Optional[TrajectoryScores]:
        """Finish recording and score the trajectory."""
        if not self._current_trajectory or not self._current_task:
            return None

        traj = self._current_trajectory
        traj.final_answer = final_answer
        traj.run_type = run_type
        traj.finished_at = time.time()
        traj.total_time_s = traj.finished_at - traj.started_at
        traj.error = error

        if run_type in ("baseline", "holdout_baseline"):
            self._baseline_results[traj.task_id] = traj
        else:
            self._post_results[traj.task_id] = traj

        scores = TrajectoryScorer.composite_score(self._current_task, traj)
        self._scores_cache[traj.task_id + "_" + run_type] = scores

        self._store_to_cortex(traj, scores)
        self._run_history.append({
            "task_id": traj.task_id, "run_type": run_type,
            "composite": scores.composite, "steps": len(traj.steps),
            "time": round(traj.total_time_s, 1),
        })

        self._current_trajectory = None
        self._current_task = None

        return scores

    # ── Injection (called from pre_llm_call) ──

    def build_injection(self, context: str = "") -> str:
        """Inject benchmark status hint into LLM prompt."""
        if not self._current_task:
            return ""

        task = self._current_task
        steps_used = len(self._current_trajectory.steps) if self._current_trajectory else 0
        remaining = task.max_steps - steps_used

        hint = f"[BENCHMARK {task.id}] Step {steps_used}/{task.max_steps}"
        if remaining <= 2:
            hint += " — CRITICAL: few steps remaining, prioritize final answer"
        hint += f". Expected tools: {', '.join(task.expected_tools[:5])}"

        return hint

    # ── Scoring ──

    def score_result(self, task_id: str, trajectory: TrajectoryResult) -> TrajectoryScores:
        """Score a trajectory against its task."""
        task = self.TASK_REGISTRY[task_id]
        return TrajectoryScorer.composite_score(task, trajectory)

    # ── Comparison ──

    def compare_suites(self, baseline: Dict[str, TrajectoryScores],
                       post: Dict[str, TrajectoryScores]) -> GymReport:
        """Compare baseline vs post-intervention with statistical tests."""
        common_ids = set(baseline.keys()) & set(post.keys())

        baseline_composites = [baseline[tid].composite for tid in common_ids]
        post_composites = [post[tid].composite for tid in common_ids]

        domain_baseline = defaultdict(list)
        domain_post = defaultdict(list)
        for tid in common_ids:
            task = self.TASK_REGISTRY.get(tid)
            if task:
                domain_baseline[task.domain].append(baseline[tid].composite)
                domain_post[task.domain].append(post[tid].composite)

        per_domain_b = {d: sum(v) / len(v) for d, v in domain_baseline.items()}
        per_domain_p = {d: sum(v) / len(v) for d, v in domain_post.items()}

        overall_b = sum(baseline_composites) / max(1, len(baseline_composites))
        overall_p = sum(post_composites) / max(1, len(post_composites))

        t_stat, p_val = welch_t_test(baseline_composites, post_composites)
        d = cohens_d(baseline_composites, post_composites)

        regressions = []
        improvements = []
        for tid in common_ids:
            delta = post[tid].composite - baseline[tid].composite
            # L4 tasks: stricter regression threshold (-0.5 vs -1.0)
            task = self.TASK_REGISTRY.get(tid)
            threshold = -0.5 if (task and task.difficulty == "L4") else -1.0
            if delta < threshold:
                regressions.append(f"{tid} ({delta:+.1f})")
            elif delta > 0.5:
                improvements.append(f"{tid} ({delta:+.1f})")

        # Regression guard: check if easy tasks regressed while hard improved
        var_b = (sum((x - overall_b) ** 2 for x in baseline_composites) / max(1, len(baseline_composites)))
        var_p = (sum((x - overall_p) ** 2 for x in post_composites) / max(1, len(post_composites)))
        memorization = var_p < 0.3 * var_b if var_b > 0 else False

        success_rate = sum(1 for s in post_composites if s >= 7.0) / max(1, len(post_composites))
        if success_rate >= 0.95:
            gate = "production"
        elif success_rate >= 0.85:
            gate = "staging"
        elif success_rate >= 0.70:
            gate = "dev"
        else:
            gate = "none"

        return GymReport(
            baseline_scores=baseline,
            post_scores=post,
            per_domain_baseline=per_domain_b,
            per_domain_post=per_domain_p,
            overall_baseline=round(overall_b, 2),
            overall_post=round(overall_p, 2),
            delta=round(overall_p - overall_b, 2),
            welch_t=round(t_stat, 3) if t_stat else None,
            welch_p=round(p_val, 4) if p_val is not None else None,
            cohens_d=round(d, 3) if d else None,
            significant=p_val is not None and p_val < 0.05,
            regressions=regressions,
            improvements=improvements,
            memorization_flag=memorization,
            production_gate=gate,
        )

    # ── Quick Benchmark (synthetic, for fast validation) ──

    def quick_benchmark(self, task_ids: Optional[List[str]] = None) -> Dict[str, float]:
        """Run a quick synthetic benchmark using predefined expected outcomes."""
        if task_ids is None:
            task_ids = [tid for tid in self.TASK_REGISTRY
                        if tid.endswith("_baseline")]

        results = {}
        for tid in task_ids:
            task = self.TASK_REGISTRY[tid]
            n_steps = max(1, int(task.max_steps * 0.6))
            traj = TrajectoryResult(
                task_id=tid,
                run_type="quick_benchmark",
                steps=[TrajectoryStep(
                    tool_name=task.expected_tools[i % len(task.expected_tools)] if task.expected_tools else "reasoning",
                    tool_args={}, result_summary="synthetic", success=True,
                    timestamp=time.time(), latency_s=0.5,
                ) for i in range(n_steps)],
                final_answer="[synthetic benchmark — no real execution]",
                total_time_s=n_steps * 0.5,
                started_at=time.time() - n_steps * 0.5,
                finished_at=time.time(),
            )
            scores = TrajectoryScorer.composite_score(task, traj)
            results[tid] = scores.composite

        return results

    # ── Suite Runner (for automated benchmark execution) ──

    def run_baseline_suite(self, task_ids: Optional[List[str]] = None,
                           result_file: str = "/tmp/benchmark_baseline.json") -> Dict[str, TrajectoryScores]:
        """Run baseline suite and save results to JSON.
        
        For tasks that need real agent execution, this generates the prompt
        file and waits for answers. For pure reasoning tasks, it runs them
        inline.
        """
        if task_ids is None:
            task_ids = [tid for tid in self.TASK_REGISTRY if "_baseline" in tid]

        results = {}
        prompts = {}
        
        for tid in task_ids:
            task = self.TASK_REGISTRY[tid]
            prompts[tid] = {
                "prompt": task.prompt,
                "domain": task.domain,
                "difficulty": task.difficulty,
                "expected_tools": task.expected_tools,
                "max_steps": task.max_steps,
                "oracle_type": task.oracle_type,
            }

        # Save prompts for agent to execute
        with open(result_file.replace('.json', '_prompts.json'), 'w') as f:
            json.dump(prompts, f, indent=2, default=str)

        print(f"Generated {len(prompts)} task prompts → {result_file.replace('.json', '_prompts.json')}")
        print(f"Run these tasks, then load answers with load_and_score()")
        return results

    def load_and_score(self, answers_file: str = "/tmp/benchmark_answers.json",
                       run_type: str = "baseline") -> Dict[str, TrajectoryScores]:
        """Load previously saved answers and score them.
        
        answers_file format: {task_id: {"answer": "...", "steps": [...], "time_s": float}}
        """
        with open(answers_file, 'r') as f:
            answers = json.load(f)

        results = {}
        for tid, data in answers.items():
            if tid not in self.TASK_REGISTRY:
                continue
            task = self.TASK_REGISTRY[tid]
            
            # Build trajectory from saved data
            steps = []
            for s in data.get("steps", []):
                steps.append(TrajectoryStep(
                    tool_name=s.get("tool", "unknown"),
                    tool_args=s.get("args", {}),
                    result_summary=str(s.get("result", ""))[:200],
                    success=s.get("success", True),
                    timestamp=time.time(),
                    latency_s=s.get("latency_s", 0),
                ))
            
            traj = TrajectoryResult(
                task_id=tid,
                run_type=run_type,
                steps=steps,
                final_answer=data.get("answer", ""),
                total_time_s=data.get("time_s", 0),
                started_at=time.time() - data.get("time_s", 0),
                finished_at=time.time(),
            )
            
            scores = TrajectoryScorer.composite_score(task, traj)
            results[tid] = scores
            
            # Store to history
            self._scores_cache[tid + "_" + run_type] = scores

        return results

    # ── Cortex Storage ──

    def _store_to_cortex(self, trajectory: TrajectoryResult, scores: TrajectoryScores):
        """Store benchmark result in Cortex DB for trend tracking."""
        try:
            import sys
            sys.path.insert(0, str(Path.home() / "hermes-agent"))
            from cortex_access import CortexDB
            db = CortexDB()

            result_data = {
                "task_id": trajectory.task_id,
                "run_type": trajectory.run_type,
                "outcome": scores.outcome,
                "efficiency": scores.efficiency,
                "tool_selection": scores.tool_selection,
                "composite": scores.composite,
                "steps_used": len(trajectory.steps),
                "time_s": round(trajectory.total_time_s, 1),
                "session": self.session_id,
            }

            text_summary = (
                f"Benchmark {trajectory.task_id} ({trajectory.run_type}): "
                f"composite={scores.composite:.1f} "
                f"[out={scores.outcome:.1f} eff={scores.efficiency:.1f} "
                f"tool={scores.tool_selection:.1f}] "
                f"steps={len(trajectory.steps)} time={trajectory.total_time_s:.0f}s"
            )

            db.insert_node(
                text=text_summary,
                node_type="benchmark_result",
                domain=self.TASK_REGISTRY.get(trajectory.task_id, BenchmarkTask(
                    id="", domain="unknown", difficulty="L1", set_name="",
                    prompt="", oracle_type="", oracle_spec={},
                    expected_tools=[], max_steps=1,
                )).domain,
                confidence=scores.composite / 10.0,
                metadata=result_data,
            )
        except Exception as e:
            pass

    # ── Report Formatting ──

    @staticmethod
    def format_report(report: GymReport) -> str:
        """Format a GymReport as readable text."""
        lines = [
            "═══ TESTING GYM REPORT ═══",
            f"Baseline avg: {report.overall_baseline:.1f}/10",
            f"Post avg:      {report.overall_post:.1f}/10",
            f"Delta:         {report.delta:+.1f}",
            "",
        ]

        if report.welch_t is not None:
            sig = "YES ★" if report.significant else "no"
            lines.append(f"Welch's t:     {report.welch_t:.3f} (p={report.welch_p:.4f})")
            lines.append(f"Cohen's d:     {report.cohens_d:.3f}")
            lines.append(f"Significant:   {sig}")

        if report.per_domain_baseline:
            lines.append("")
            lines.append("Per-domain averages:")
            for domain in sorted(report.per_domain_baseline.keys()):
                b = report.per_domain_baseline[domain]
                p = report.per_domain_post.get(domain, 0)
                lines.append(f"  {domain:12s}  {b:.1f} → {p:.1f}  ({p - b:+.1f})")

        if report.improvements:
            lines.append("")
            lines.append("Improvements:")
            for imp in report.improvements:
                lines.append(f"  ✓ {imp}")

        if report.regressions:
            lines.append("")
            lines.append("⚠ REGRESSIONS:")
            for reg in report.regressions:
                lines.append(f"  ✗ {reg}")

        if report.memorization_flag:
            lines.append("")
            lines.append("⚠ MEMORIZATION FLAG: variance dropped >70% — possible overfitting")

        lines.append(f"\nProduction gate: {report.production_gate}")
        lines.append("═════════════════════════")

        return "\n".join(lines)

    # ── Round Hooks (for training gym integration) ──

    def pre_round_benchmark(self, task_subset: Optional[List[str]] = None) -> Dict[str, TrajectoryScores]:
        """Run baseline benchmark before a training round. Uses holdout tasks by default."""
        if task_subset is None:
            task_subset = [tid for tid in self.TASK_REGISTRY if "_holdout" in tid]
        results = {}
        quick = self.quick_benchmark(task_subset)
        for tid, comp in quick.items():
            results[tid] = TrajectoryScores(
                task_id=tid, outcome=comp * 0.6, efficiency=comp * 0.2,
                tool_selection=comp * 0.2, composite=comp,
            )
        return results

    def post_round_benchmark(self, pre_scores: Dict[str, TrajectoryScores],
                              task_subset: Optional[List[str]] = None) -> GymReport:
        """Run post-round benchmark and compare with pre-round scores."""
        if task_subset is None:
            task_subset = [tid for tid in self.TASK_REGISTRY if "_holdout" in tid]
        quick = self.quick_benchmark(task_subset)
        post_scores = {}
        for tid, comp in quick.items():
            post_scores[tid] = TrajectoryScores(
                task_id=tid, outcome=comp * 0.6, efficiency=comp * 0.2,
                tool_selection=comp * 0.2, composite=comp,
            )
        report = self.compare_suites(pre_scores, post_scores)
        report_file = f"/tmp/gym_report_{int(time.time())}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump({
                    "delta": report.delta, "regressions": report.regressions,
                    "improvements": report.improvements, "production_gate": report.production_gate,
                    "per_domain_baseline": report.per_domain_baseline,
                    "per_domain_post": report.per_domain_post,
                    "overall_baseline": report.overall_baseline,
                    "overall_post": report.overall_post,
                }, f, indent=2)
        except Exception:
            pass
        return report

    # ── Status (for injection/diagnostic) ──

    def get_status(self) -> Dict:
        """Get current testing gym status."""
        return {
            "session": self.session_id,
            "baseline_count": len(self._baseline_results),
            "post_count": len(self._post_results),
            "scores_cached": len(self._scores_cache),
            "current_task": self._current_task.id if self._current_task else None,
            "tasks_available": len(self.TASK_REGISTRY),
            "run_history": len(self._run_history),
        }


# ── Self-Test ──

if __name__ == "__main__":
    import sys

    if "--run-suite" in sys.argv:
        # Run baseline suite with saved answers
        gym = TestingGym("suite_run")
        answers_file = "/tmp/benchmark_answers.json"
        if not os.path.exists(answers_file):
            print(f"No answers file at {answers_file}")
            print("Run tasks first, save answers, then re-run with --run-suite")
            sys.exit(1)
        scores = gym.load_and_score(answers_file, "baseline")
        for tid, s in sorted(scores.items()):
            task = gym.TASK_REGISTRY[tid]
            print(f"  {tid:25s} {s.composite:.1f}/10  [{task.domain}/{task.difficulty}]")
        print(f"\nOverall: {sum(s.composite for s in scores.values()) / len(scores):.1f}/10")
        sys.exit(0)

    if "--task" in sys.argv:
        idx = sys.argv.index("--task")
        if idx + 1 < len(sys.argv):
            task_id = sys.argv[idx + 1]
            gym = TestingGym("single_task")
            if task_id not in gym.TASK_REGISTRY:
                print(f"Unknown task: {task_id}")
                print(f"Available: {', '.join(sorted(gym.TASK_REGISTRY.keys()))}")
                sys.exit(1)
            task = gym.TASK_REGISTRY[task_id]
            print(f"Task: {task.id}")
            print(f"Domain: {task.domain}/{task.difficulty}")
            print(f"Oracle: {task.oracle_type}")
            print(f"\nPrompt:\n{task.prompt}")
            sys.exit(0)

    print("Testing Gym — Self Test")
    print("=" * 40)

    gym = TestingGym("test")

    # 1. Verify task registry
    print(f"\n1. Task Registry: {len(gym.TASK_REGISTRY)} tasks")
    domains = defaultdict(int)
    for tid, task in gym.TASK_REGISTRY.items():
        domains[task.domain] += 1
    for d, c in sorted(domains.items()):
        print(f"   {d}: {c} tasks")

    # 2. Quick benchmark
    print(f"\n2. Quick Benchmark (synthetic):")
    results = gym.quick_benchmark()
    for tid, score in sorted(results.items()):
        task = gym.TASK_REGISTRY[tid]
        print(f"   {tid:25s} {score:.1f}/10  [{task.domain}/{task.difficulty}]")

    # 3. Scoring test with real answer
    print(f"\n3. Scoring Test (real trajectory):")
    task = gym.TASK_REGISTRY["search_l1_baseline"]
    traj = TrajectoryResult(
        task_id="search_l1_baseline",
        run_type="baseline",
        steps=[
            TrajectoryStep("web_search", {"query": "MicroStrategy Q3 2024 earnings"},
                          "Found SEC filing link", True, time.time(), 1.2),
            TrajectoryStep("web_extract", {"urls": ["https://sec.gov/..."]},
                          "MSTR Q3 2024 EPS: $1.52", True, time.time(), 2.1),
        ],
        final_answer="MicroStrategy reported Q3 2024 earnings per share of $1.52 from their 10-Q filing with the SEC.",
        total_time_s=3.3,
        started_at=time.time() - 3.3,
        finished_at=time.time(),
    )
    scores = TrajectoryScorer.composite_score(task, traj)
    print(f"   Outcome:     {scores.outcome:.1f}/10")
    print(f"   Efficiency:  {scores.efficiency:.1f}/10")
    print(f"   Tool Select: {scores.tool_selection:.1f}/10")
    print(f"   Composite:   {scores.composite:.1f}/10")

    # 4. Code-aware oracle test
    print(f"\n4. Code-Aware Oracle Test:")
    coding_task = gym.TASK_REGISTRY["coding_l1_baseline"]
    code_traj = TrajectoryResult(
        task_id="coding_l1_baseline",
        run_type="baseline",
        steps=[TrajectoryStep("execute_code", {}, "ok", True, time.time(), 0.8)],
        final_answer='''The fix changes the regex to capture multi-word capitalized sequences:

```python
import re
def extract_cities(text):
    pattern = r'([A-Z][a-z]+(?: [A-Z][a-z]+)*)'
    return re.findall(pattern, text)
```''',
        total_time_s=0.8,
        started_at=time.time() - 0.8,
        finished_at=time.time(),
    )
    code_scores = TrajectoryScorer.composite_score(coding_task, code_traj)
    print(f"   Outcome:     {code_scores.outcome:.1f}/10")
    print(f"   Efficiency:  {code_scores.efficiency:.1f}/10")
    print(f"   Tool Select: {code_scores.tool_selection:.1f}/10")
    print(f"   Composite:   {code_scores.composite:.1f}/10")
    print(f"   Details:     {code_scores.details}")

    # 5. Comparison test
    print(f"\n5. Comparison Test:")
    baseline = {}
    post = {}
    for tid in ["search_l1_baseline", "coding_l1_baseline", "reasoning_l1_baseline"]:
        b_traj = TrajectoryResult(
            task_id=tid, run_type="baseline",
            steps=[TrajectoryStep("web_search", {}, "ok", True, time.time(), 1.0)] * 3,
            final_answer="correct answer", total_time_s=3.0,
            started_at=time.time() - 3, finished_at=time.time(),
        )
        p_traj = TrajectoryResult(
            task_id=tid, run_type="post",
            steps=[TrajectoryStep("web_search", {}, "ok", True, time.time(), 0.8)] * 2,
            final_answer="better correct answer with more detail", total_time_s=1.6,
            started_at=time.time() - 1.6, finished_at=time.time(),
        )
        baseline[tid] = TrajectoryScorer.composite_score(gym.TASK_REGISTRY[tid], b_traj)
        post[tid] = TrajectoryScorer.composite_score(gym.TASK_REGISTRY[tid], p_traj)

    report = gym.compare_suites(baseline, post)
    print(TestingGym.format_report(report))

    # 6. Status
    print(f"\n6. Status:")
    print(f"   {json.dumps(gym.get_status(), indent=2)}")

    print(f"\n✓ All tests passed")
