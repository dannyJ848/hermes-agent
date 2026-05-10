#!/usr/bin/env python3
"""
Skill Effectiveness Tracker — v1.0
Tracks real-world success rates of skills and auto-archives underperformers.

DESIGN:
  - Scans ~/.hermes/skills/ for all installed skills
  - Cross-references with iteration engine experiences where action_type starts with "skill_"
  - Also parses run-history for skill usage patterns
  - Calculates rolling success rate per skill
  - Flags skills below 60% success rate for archival
  - Generates a report suitable for the agent's self-improvement loop

INTEGRATION:
  - Called by the subconscious brain cycle during "grow" phase
  - Results feed into governance validator for archival decisions
  - Stats exposed via get_skill_report() for Dojo sessions
"""

import json
import re
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SKILLS_DIR = Path.home() / ".hermes" / "skills"
EXPERIENCES_DB = Path.home() / ".hermes" / "cerebrum_memory.db"
TRACKER_DB = Path.home() / ".hermes" / "skill_effectiveness.db"

ARCHIVE_THRESHOLD = 0.60  # Below this success rate, flag for archival
MIN_OBSERVATIONS = 3       # Need at least N observations before judging
ROLLING_WINDOW_DAYS = 30   # Only look at last N days for rate calculation


class SkillEffectivenessTracker:
    """Track and evaluate skill performance based on real usage data."""

    def __init__(self, skills_dir: Path = SKILLS_DIR,
                 experiences_db: Path = EXPERIENCES_DB,
                 tracker_db: Path = TRACKER_DB):
        self.skills_dir = skills_dir
        self.experiences_db = experiences_db
        self.tracker_db = tracker_db
        self._ensure_tracker_db()

    def _ensure_tracker_db(self):
        """Create the skill effectiveness tables."""
        conn = sqlite3.connect(str(self.tracker_db))
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS skill_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                timestamp REAL NOT NULL,
                outcome TEXT NOT NULL,  -- success, failure, partial
                context TEXT DEFAULT '',
                duration_ms INTEGER DEFAULT 0,
                source TEXT DEFAULT 'iteration_engine'  -- iteration_engine, manual, cron
            );

            CREATE TABLE IF NOT EXISTS skill_scores (
                skill_name TEXT PRIMARY KEY,
                total_uses INTEGER DEFAULT 0,
                successes INTEGER DEFAULT 0,
                failures INTEGER DEFAULT 0,
                partials INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                last_used REAL DEFAULT 0,
                last_scored REAL DEFAULT 0,
                flagged_for_archive INTEGER DEFAULT 0,
                archive_reason TEXT DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_obs_skill ON skill_observations(skill_name);
            CREATE INDEX IF NOT EXISTS idx_obs_time ON skill_observations(timestamp);
            CREATE INDEX IF NOT EXISTS idx_score_flag ON skill_scores(flagged_for_archive);
        """)
        conn.commit()
        conn.close()

    def _get_connection(self, db_path: Path) -> sqlite3.Connection:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def scan_installed_skills(self) -> List[Dict]:
        """Scan ~/.hermes/skills/ and return all installed skills with metadata."""
        skills = []
        if not self.skills_dir.exists():
            return skills

        for skill_dir in sorted(self.skills_dir.rglob("SKILL.md")):
            skill_parent = skill_dir.parent
            # Category is relative path from skills_dir to the skill's parent
            rel = skill_parent.relative_to(self.skills_dir)
            parts = rel.parts

            if len(parts) >= 2:
                # e.g., mlops/training/grpo-rl-training
                category = "/".join(parts[:-1])
                name = parts[-1]
            elif len(parts) == 1:
                category = ""
                name = parts[0]
            else:
                continue

            # Read skill metadata from SKILL.md frontmatter
            metadata = self._parse_skill_metadata(skill_dir)
            metadata["name"] = name
            metadata["category"] = category
            metadata["path"] = str(skill_parent)
            metadata["skill_md"] = str(skill_dir)
            skills.append(metadata)

        return skills

    def _parse_skill_metadata(self, skill_md_path: Path) -> Dict:
        """Parse YAML frontmatter from a SKILL.md file."""
        metadata = {"has_trigger": False, "has_version": False, "description": ""}
        try:
            content = skill_md_path.read_text(errors="ignore")
            # Simple frontmatter parser
            if content.startswith("---"):
                end = content.find("---", 3)
                if end > 0:
                    fm = content[3:end].strip()
                    for line in fm.split("\n"):
                        if line.startswith("name:"):
                            metadata["yaml_name"] = line.split(":", 1)[1].strip()
                        elif line.startswith("version:"):
                            metadata["has_version"] = True
                            metadata["version"] = line.split(":", 1)[1].strip()
                        elif line.startswith("description:"):
                            metadata["description"] = line.split(":", 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("trigger:"):
                            metadata["has_trigger"] = True
                            metadata["trigger"] = line.split(":", 1)[1].strip()
        except Exception:
            pass
        return metadata

    def ingest_iteration_engine_data(self) -> int:
        """
        Pull skill-related experiences from the iteration engine
        and record them as observations.

        Returns number of new observations ingested.
        """
        if not self.experiences_db.exists():
            return 0

        try:
            src_conn = self._get_connection(self.experiences_db)
        except Exception:
            return 0

        # Get skill-related experiences
        # Skills are used via skill_view, skill_manage, or action_type contains "skill"
        rows = src_conn.execute("""
            SELECT action_type, action_detail, result, last_seen, speed_ms
            FROM experiences
            WHERE action_type LIKE '%skill%' OR action_detail LIKE '%skill%'
            ORDER BY last_seen DESC
        """).fetchall()
        src_conn.close()

        if not rows:
            return 0

        # Record into tracker
        dst_conn = sqlite3.connect(str(self.tracker_db))
        ingested = 0
        for row in rows:
            action_type = row["action_type"]
            action_detail = row["action_detail"]
            result = row["result"]
            last_seen = row["last_seen"] or 0
            speed_ms = row["speed_ms"] or 0

            # Extract skill name from detail
            skill_name = self._extract_skill_name(action_type, action_detail)
            if not skill_name:
                continue

            # Check if we already have this observation (dedup by last_seen + skill + result)
            existing = dst_conn.execute(
                "SELECT id FROM skill_observations WHERE skill_name=? AND timestamp=? AND outcome=?",
                (skill_name, last_seen, result)
            ).fetchone()

            if not existing:
                dst_conn.execute("""
                    INSERT INTO skill_observations (skill_name, timestamp, outcome, context, duration_ms, source)
                    VALUES (?, ?, ?, ?, ?, 'iteration_engine')
                """, (skill_name, last_seen, result, f"{action_type}: {action_detail}", speed_ms))
                ingested += 1

        dst_conn.commit()
        dst_conn.close()
        return ingested

    def _extract_skill_name(self, action_type: str, detail: str) -> Optional[str]:
        """Extract skill name from action details."""
        # Patterns: "skill_view(name='xxx')" or "viewed skill xxx" or detail contains skill path
        patterns = [
            r"skill[_-]?(?:view|manage|load|use|run)[\s(]*(?:name=['\"]?|)([a-z0-9_-]+)",
            r"skills?[/\\]([a-z0-9_-]+)",
            r"(?:loaded|using|running)\s+skill[:\s]+([a-z0-9_-]+)",
        ]
        for pat in patterns:
            m = re.search(pat, f"{action_type} {detail}", re.IGNORECASE)
            if m:
                return m.group(1).lower()
        return None

    def record_observation(self, skill_name: str, outcome: str,
                           context: str = "", duration_ms: int = 0,
                           source: str = "manual"):
        """Record a skill usage observation."""
        conn = sqlite3.connect(str(self.tracker_db))
        conn.execute("""
            INSERT INTO skill_observations (skill_name, timestamp, outcome, context, duration_ms, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (skill_name.lower(), time.time(), outcome, context, duration_ms, source))
        conn.commit()
        conn.close()

    def recalculate_scores(self) -> Dict[str, Dict]:
        """
        Recalculate rolling success rates for all skills.
        Returns dict of skill_name -> score_info.
        """
        conn = self._get_connection(self.tracker_db)
        cutoff = time.time() - (ROLLING_WINDOW_DAYS * 86400)

        # Get all observations in rolling window
        rows = conn.execute("""
            SELECT skill_name, outcome, COUNT(*) as cnt
            FROM skill_observations
            WHERE timestamp >= ?
            GROUP BY skill_name, outcome
        """, (cutoff,)).fetchall()

        # Aggregate per skill
        skill_data = defaultdict(lambda: {"success": 0, "failure": 0, "partial": 0})
        for row in rows:
            skill_data[row["skill_name"]][row["outcome"]] = row["cnt"]

        # Get last used timestamp per skill
        last_used = {}
        for row in conn.execute("""
            SELECT skill_name, MAX(timestamp) as last_t
            FROM skill_observations
            GROUP BY skill_name
        """).fetchall():
            last_used[row["skill_name"]] = row["last_t"]

        # Calculate scores and update
        now = time.time()
        results = {}

        for skill_name, counts in skill_data.items():
            total = counts["success"] + counts["failure"] + counts["partial"]
            if total == 0:
                continue

            success_rate = counts["success"] / total if total > 0 else 0.0
            flagged = 1 if (total >= MIN_OBSERVATIONS and success_rate < ARCHIVE_THRESHOLD) else 0
            archive_reason = ""
            if flagged:
                archive_reason = f"Success rate {success_rate:.0%} below {ARCHIVE_THRESHOLD:.0%} threshold ({total} observations)"

            conn.execute("""
                INSERT OR REPLACE INTO skill_scores
                (skill_name, total_uses, successes, failures, partials, success_rate,
                 last_used, last_scored, flagged_for_archive, archive_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                skill_name, total, counts["success"], counts["failure"],
                counts["partial"], success_rate, last_used.get(skill_name, 0),
                now, flagged, archive_reason
            ))

            results[skill_name] = {
                "total": total,
                "success_rate": round(success_rate, 3),
                "flagged": flagged,
                "archive_reason": archive_reason,
            }

        conn.commit()
        conn.close()
        return results

    def get_flagged_skills(self) -> List[Dict]:
        """Get skills flagged for archival."""
        conn = self._get_connection(self.tracker_db)
        rows = conn.execute("""
            SELECT * FROM skill_scores
            WHERE flagged_for_archive = 1
            ORDER BY success_rate ASC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_skill_report(self) -> Dict:
        """
        Generate a comprehensive skill effectiveness report.

        Returns:
            - total_installed: number of skills found
            - total_tracked: skills with usage data
            - high_performers: skills with >80% success rate
            - underperformers: skills below 60% success rate
            - unused: installed skills with zero observations
            - top_skills: most frequently used
            - recommendations: actions to take
        """
        installed = self.scan_installed_skills()
        installed_names = {s["name"] for s in installed}
        installed_by_cat = defaultdict(list)
        for s in installed:
            installed_by_cat[s["category"]].append(s["name"])

        conn = self._get_connection(self.tracker_db)

        # Get all scored skills
        scored = {}
        for row in conn.execute("SELECT * FROM skill_scores"):
            scored[row["skill_name"]] = dict(row)
        conn.close()

        # Classify
        high_performers = []
        underperformers = []
        unused = []

        for name in sorted(installed_names):
            if name in scored:
                s = scored[name]
                if s["success_rate"] >= 0.80:
                    high_performers.append(s)
                elif s["success_rate"] < ARCHIVE_THRESHOLD and s["total_uses"] >= MIN_OBSERVATIONS:
                    underperformers.append(s)
            else:
                # Check if any variant of the name is tracked
                found = False
                for tracked_name in scored:
                    if name.replace("-", "_") in tracked_name or tracked_name in name.replace("-", "_"):
                        found = True
                        break
                if not found:
                    unused.append({"name": name, "status": "no_observations"})

        # Top by usage
        top_by_usage = sorted(scored.values(), key=lambda x: x.get("total_uses", 0), reverse=True)[:10]

        # Recommendations
        recommendations = []
        for s in underperformers:
            recommendations.append({
                "action": "archive_or_fix",
                "skill": s["skill_name"],
                "reason": s.get("archive_reason", "Low success rate"),
                "suggestion": f"Review skill for accuracy or archive. Success: {s.get('success_rate', 0):.0%} over {s.get('total_uses', 0)} uses."
            })
        for s in unused[:5]:
            recommendations.append({
                "action": "evaluate_or_remove",
                "skill": s["name"],
                "reason": "No usage data found",
                "suggestion": "Evaluate if skill is still needed. If unused for 30+ days, consider removal."
            })

        return {
            "timestamp": datetime.now().isoformat(),
            "total_installed": len(installed_names),
            "categories": {k: len(v) for k, v in installed_by_cat.items() if k},
            "total_tracked": len(scored),
            "high_performers": high_performers,
            "underperformers": underperformers,
            "unused": unused,
            "top_by_usage": top_by_usage,
            "recommendations": recommendations,
        }

    def print_report(self):
        """Print a human-readable report."""
        report = self.get_skill_report()

        print("═" * 60)
        print("  SKILL EFFECTIVENESS REPORT")
        print(f"  {report['timestamp']}")
        print("═" * 60)
        print(f"\n  Total installed: {report['total_installed']}")
        print(f"  Total tracked:   {report['total_tracked']}")

        if report["categories"]:
            print("\n  Categories:")
            for cat, count in sorted(report["categories"].items()):
                print(f"    {cat}: {count} skills")

        if report["high_performers"]:
            print(f"\n  ✅ HIGH PERFORMERS (>80% success):")
            for s in report["high_performers"]:
                print(f"    {s['skill_name']}: {s['success_rate']:.0%} ({s['total_uses']} uses)")

        if report["underperformers"]:
            print(f"\n  ⚠️  UNDERPERFORMERS (<60% success, >={MIN_OBSERVATIONS} observations):")
            for s in report["underperformers"]:
                print(f"    {s['skill_name']}: {s['success_rate']:.0%} ({s['total_uses']} uses)")
                if s.get("archive_reason"):
                    print(f"      → {s['archive_reason']}")

        if report["unused"]:
            print(f"\n  📭 UNUSED (no observations):")
            for s in report["unused"][:10]:
                print(f"    {s['name']}")

        if report["top_by_usage"]:
            print(f"\n  📊 TOP BY USAGE:")
            for s in report["top_by_usage"][:5]:
                print(f"    {s['skill_name']}: {s['total_uses']} uses, {s['success_rate']:.0%} success")

        if report["recommendations"]:
            print(f"\n  🔧 RECOMMENDATIONS:")
            for r in report["recommendations"]:
                print(f"    [{r['action'].upper()}] {r['skill']}: {r['suggestion']}")

        print("\n" + "═" * 60)


def run_tracking_cycle():
    """Full cycle: ingest data → recalculate → report."""
    tracker = SkillEffectivenessTracker()

    # Step 1: Scan installed skills
    installed = tracker.scan_installed_skills()
    print(f"Scanned {len(installed)} installed skills")

    # Step 2: Ingest iteration engine data
    ingested = tracker.ingest_iteration_engine_data()
    print(f"Ingested {ingested} new observations from iteration engine")

    # Step 3: Recalculate scores
    scores = tracker.recalculate_scores()
    print(f"Recalculated scores for {len(scores)} skills")

    # Step 4: Print report
    tracker.print_report()

    return tracker.get_skill_report()


if __name__ == "__main__":
    run_tracking_cycle()
