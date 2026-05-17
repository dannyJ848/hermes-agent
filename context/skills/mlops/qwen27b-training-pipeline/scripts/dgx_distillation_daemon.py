#!/usr/bin/env python3
"""
DGX Distillation Daemon v2
Fixed: Extracts lessons from BOTH successes and failures.
"""

import sqlite3
import time
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


def extract_lesson_from_success(action_type, action_detail, result):
    """Extract a positive lesson from a successful experience."""
    lessons = {
        'terminal': 'Use terminal for shell commands, builds, git. Set timeout=300+ for long tasks.',
        'execute_code': 'Use execute_code for Python scripts with 3+ tool calls. Print final result.',
        'skill_view': 'Load skills proactively with skill_view(name) before matching tasks.',
        'skill_manage': 'Save successful workflows as skills. Patch existing skills when pitfalls found.',
        'read_file': 'Use read_file instead of cat/head/tail. Use offset/limit for large files.',
        'write_file': 'Use write_file instead of echo/heredoc. Auto-runs syntax checks.',
        'patch': 'Use patch for targeted edits. Include enough context for uniqueness.',
        'search_files': 'Use search_files instead of grep/find. Use target=files for directory listing.',
        'delegate_task': 'Delegate reasoning-heavy subtasks. Provide full context.',
        'delegate_with_model': 'Use cheap models for simple tasks. Route code to qwen-coder-free.',
        'web_search': 'Use web_search for current info, fact verification.',
        'web_extract': 'Use web_extract for articles, docs. Use max_chars to limit output.',
        'browser_navigate': 'Use browser_navigate first, then click/type/scroll.',
        'memory': 'Save user preferences, environment facts, tool quirks to memory.',
        'learn_from_interaction': 'Call after delegation, research, or non-trivial tool use.',
        'status_check': 'Call status_check FIRST every session. Free - shows bridge, costs, cron.',
        'cost_check': 'Check cost_check BEFORE expensive operations.',
    }
    return lessons.get(action_type, f'{action_type} worked successfully - note pattern for reuse')


def extract_lesson_from_failure(action_type, error_pattern, result):
    """Extract a lesson from a failed experience."""
    if not error_pattern:
        return None
    
    if 'TIMEOUT' in error_pattern:
        return 'Increase timeout or break the task into smaller steps'
    elif 'AUTH' in error_pattern or 'forbidden' in error_pattern.lower():
        return 'Check API keys and credentials. Verify endpoint is accessible.'
    elif 'REGRESSION' in result:
        return f'Avoid: {error_pattern[:200]}'
    elif 'not found' in error_pattern.lower():
        return 'Verify file paths and URLs before accessing'
    elif 'permission' in error_pattern.lower():
        return 'Check file permissions and ownership'
    else:
        return f'Avoid: {error_pattern[:200]}'


def backfill_missing_lessons():
    """Extract lessons for experiences that don't have them."""
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    
    cursor = conn.execute(
        """SELECT id, action_type, result, error_pattern, action_detail
           FROM experiences 
           WHERE lesson = '' OR lesson IS NULL"""
    )
    
    updated = 0
    for row in cursor.fetchall():
        exp_id, action_type, result, error_pattern, action_detail = row
        
        if result == 'regression' or error_pattern:
            lesson = extract_lesson_from_failure(action_type, error_pattern, result)
        else:
            lesson = extract_lesson_from_success(action_type, action_detail, result)
        
        if lesson:
            conn.execute(
                "UPDATE experiences SET lesson = ? WHERE id = ?",
                (lesson, exp_id)
            )
            updated += 1
    
    conn.commit()
    conn.close()
    
    return updated


def distill_experiences(min_freq=2):
    """Convert experiences into tips."""
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # First backfill any missing lessons
    backfill_missing_lessons()
    
    # Find experiences that have happened min_freq+ times with lessons
    cursor = conn.execute(
        """SELECT action_type, result, lesson, frequency, action_detail
           FROM experiences 
           WHERE frequency >= ? AND lesson != '' AND lesson IS NOT NULL
           ORDER BY frequency DESC""",
        (min_freq,)
    )
    
    new_tips = 0
    for row in cursor.fetchall():
        action_type, result, lesson, freq, detail = row
        
        # Create tip condition
        condition = f"Using {action_type}"
        if detail:
            try:
                args = json.loads(detail)
                if args:
                    condition += f" with args: {str(args)[:100]}"
            except:
                pass
        
        # Add result context
        if result == 'regression':
            condition += " (failure mode)"
        else:
            condition += " (success pattern)"
        
        recommendation = lesson
        
        # Check if tip already exists
        existing = conn.execute(
            "SELECT id FROM distilled_tips WHERE condition = ?",
            (condition,)
        ).fetchone()
        
        if not existing:
            conn.execute(
                """INSERT INTO distilled_tips 
                   (tip_type, condition, recommendation, tool_name, domain,
                    confidence, created_at, last_seen, frequency)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("strategy", condition, recommendation, action_type, "general",
                 min(0.5 + (freq * 0.05), 0.95), time.time(), time.time(), freq)
            )
            new_tips += 1
    
    conn.commit()
    conn.close()
    
    return new_tips


def export_training_data():
    """Export tips as training data for Qwen."""
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    
    cursor = conn.execute(
        """SELECT condition, recommendation, confidence, tool_name
           FROM distilled_tips 
           WHERE confidence > 0.5
           ORDER BY confidence DESC"""
    )
    
    output_dir = Path("/data/SpecForge/custom_dflash/datasets/hermes_sessions")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"dgx_distilled_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
    
    count = 0
    with open(output_file, 'w') as f:
        for row in cursor.fetchall():
            condition, recommendation, confidence, tool_name = row
            
            messages = [
                {"role": "user", "content": f"When using {tool_name}, what should I watch out for?"},
                {"role": "assistant", "content": f"Pattern: {condition}\n\n"
                                                   f"Recommendation: {recommendation}\n\n"
                                                   f"This tip has confidence {confidence:.2f} based on repeated experience."}
            ]
            
            entry = {
                "messages": messages,
                "source": "dgx_distillation",
                "type": "tip",
                "quality_score": confidence,
                "timestamp": datetime.now().isoformat()
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            count += 1
    
    conn.close()
    
    return count, str(output_file)


def main():
    """Main daemon loop."""
    print("DGX Distillation Daemon v2 started")
    print(f"Database: {DB_PATH}")
    
    # Initial backfill
    print("Backfilling missing lessons...")
    backfilled = backfill_missing_lessons()
    print(f"Backfilled {backfilled} lessons")
    
    # Initial distillation
    print("Running initial distillation...")
    new_tips = distill_experiences(min_freq=2)
    print(f"Created {new_tips} new tips")
    
    while True:
        try:
            # Distill new tips (lower threshold = 2)
            new_tips = distill_experiences(min_freq=2)
            if new_tips > 0:
                print(f"[{datetime.now()}] Created {new_tips} new tips")
            
            # Export training data every hour
            if datetime.now().minute == 0:
                count, path = export_training_data()
                if count > 0:
                    print(f"[{datetime.now()}] Exported {count} tips to {path}")
            
            # Sleep for 5 minutes
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\nDaemon stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)


if __name__ == '__main__':
    main()
