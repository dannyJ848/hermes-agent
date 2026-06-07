"""request_lesson — DGX tool to request a lesson from MacBook Hermes teacher."""

import os
from datetime import datetime, timezone
from typing import Dict, Any

from tools.registry import registry


TERMINAL_SCHEMA = {
    "type": "object",
    "properties": {
        "task": {"type": "string", "description": "Short name of the task (e.g., reddit-browser-debug)"},
        "what_went_wrong": {"type": "string", "description": "Detailed description of what failed"},
        "attempted_approaches": {"type": "string", "description": "What was already tried (optional)"},
    },
    "required": ["task", "what_went_wrong"],
}


def request_lesson(task: str, what_went_wrong: str, attempted_approaches: str = "") -> Dict[str, Any]:
    """
    Request a lesson from MacBook Hermes (teacher) when stuck on a task.
    
    Use this when:
    - Web scraping fails due to IP blocks (Reddit, etc.)
    - Browser automation is blocked by bot detection
    - A tool consistently fails after multiple attempts
    - You need knowledge MacBook has (API keys, proxies, etc.)
    
    Args:
        task: Short name of the task (e.g., "reddit-browser-debug")
        what_went_wrong: Detailed description of the failure
        attempted_approaches: What you already tried (optional)
    
    Returns:
        Dict with status and path to the request file
    """
    
    home = os.path.expanduser("~")
    request_dir = os.path.join(home, "teacher-lessons")
    os.makedirs(request_dir, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    request_file = os.path.join(request_dir, f".request-{timestamp}-{task}")
    
    content = f"""---
from: dgx-hermes
model: Qwopus3.6-27B-v2-MTP-BF16
task: {task}
date: {datetime.now(timezone.utc).isoformat()}
status: pending
---

# Lesson Request from DGX

## Task
{task}

## What Went Wrong
{what_went_wrong}

## Attempted Approaches
{attempted_approaches or "None documented"}

## DGX Context
- Model: Qwopus3.6-27B-v2-MTP-BF16
- Provider: spark-bf16 (llama.cpp)
- Date: {datetime.now().isoformat()}
"""
    
    try:
        with open(request_file, "w") as f:
            f.write(content)
        
        return {
            "status": "requested",
            "request_file": request_file,
            "task": task,
            "message": f"Lesson requested: {task}. MacBook will see this during next heartbeat."
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "task": task
        }


def check_lessons() -> Dict[str, Any]:
    """
    Check for new lessons from MacBook teacher.
    
    Returns:
        Dict with count and list of lesson files
    """
    
    home = os.path.expanduser("~")
    lesson_dir = os.path.join(home, "teacher-lessons")
    read_dir = os.path.join(lesson_dir, "read")
    
    os.makedirs(read_dir, exist_ok=True)
    
    try:
        lessons = []
        for f in os.listdir(lesson_dir):
            if f.endswith(".md") and os.path.isfile(os.path.join(lesson_dir, f)):
                lessons.append(f)
        
        return {
            "status": "ok",
            "count": len(lessons),
            "lessons": sorted(lessons),
            "lesson_dir": lesson_dir,
            "message": f"{len(lessons)} lesson(s) available. Read with: cat ~/teacher-lessons/<lesson>"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def read_lesson(lesson_name: str) -> Dict[str, Any]:
    """
    Read a specific lesson from MacBook teacher.
    
    Args:
        lesson_name: Name of the lesson file (e.g., "lesson-20260606-200359-reddit-browser-debug.md")
    
    Returns:
        Dict with lesson content and metadata
    """
    
    home = os.path.expanduser("~")
    lesson_path = os.path.join(home, "teacher-lessons", lesson_name)
    
    try:
        with open(lesson_path, "r") as f:
            content = f.read()
        
        return {
            "status": "ok",
            "lesson": lesson_name,
            "content": content,
            "path": lesson_path
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "error": f"Lesson not found: {lesson_name}",
            "available_lessons": check_lessons().get("lessons", [])
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def mark_lesson_read(lesson_name: str) -> Dict[str, Any]:
    """
    Mark a lesson as read by moving it to the read/ subdirectory.
    
    Args:
        lesson_name: Name of the lesson file
    
    Returns:
        Dict with status
    """
    
    home = os.path.expanduser("~")
    lesson_dir = os.path.join(home, "teacher-lessons")
    read_dir = os.path.join(lesson_dir, "read")
    
    os.makedirs(read_dir, exist_ok=True)
    
    src = os.path.join(lesson_dir, lesson_name)
    dst = os.path.join(read_dir, lesson_name)
    
    try:
        os.rename(src, dst)
        return {
            "status": "ok",
            "message": f"Marked as read: {lesson_name}",
            "path": dst
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def _handle_request_lesson(args: dict, task_id: str = None) -> dict:
    return request_lesson(
        task=args.get("task") or "unknown",
        what_went_wrong=args.get("what_went_wrong") or "no details",
        attempted_approaches=args.get("attempted_approaches", ""),
    )


CHECK_LESSONS_SCHEMA = {
    "type": "object",
    "properties": {},
    "required": [],
}

READ_LESSON_SCHEMA = {
    "type": "object",
    "properties": {
        "lesson_name": {"type": "string", "description": "Name of the lesson file to read"},
    },
    "required": ["lesson_name"],
}


def _handle_check_lessons(args: dict, task_id: str = None) -> dict:
    return check_lessons()


def _handle_read_lesson(args: dict, task_id: str = None) -> dict:
    return read_lesson(args.get("lesson_name") or "")


registry.register(
    name="request_lesson",
    toolset="terminal",
    schema=TERMINAL_SCHEMA,
    handler=_handle_request_lesson,
    emoji="📚",
)

registry.register(
    name="check_lessons",
    toolset="terminal",
    schema=CHECK_LESSONS_SCHEMA,
    handler=_handle_check_lessons,
    emoji="📖",
)

registry.register(
    name="read_lesson",
    toolset="terminal",
    schema=READ_LESSON_SCHEMA,
    handler=_handle_read_lesson,
    emoji="📄",
)
