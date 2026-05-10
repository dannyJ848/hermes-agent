#!/usr/bin/env python3
"""
hermes_plan_executor.py — Multi-step plan executor with retry and adaptation.

Takes a plan (list of steps), executes each, auto-retry on failure, adapts strategy.
Integrates with tool logger for full traceability.

Usage:
  from hermes_plan_executor import execute_plan, Step
  
  plan = [
      Step(tool="web_search", args={"query": "AI agents"}, retries=2),
      Step(tool="web_extract", args={"url": "{step0.results[0].url}"}, retries=1),
      Step(tool="save_finding", args={"topic": "agent research", "content": "{step1.content}"}),
  ]
  
  result = execute_plan(plan, context="research task")
"""

import json
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path

# Import tool logger if available
try:
    from hermes_tool_logger import log_tool_call, get_tool_recommendation
    TOOL_LOGGER = True
except ImportError:
    TOOL_LOGGER = False

@dataclass
class Step:
    """A single step in an execution plan."""
    tool: str
    args: dict
    description: str = ""
    retries: int = 2
    fallback_tool: Optional[str] = None
    condition: Optional[str] = None  # Skip if this evals to False
    timeout_seconds: int = 60
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.tool}({', '.join(self.args.keys())})"

@dataclass
class StepResult:
    """Result of executing a step."""
    step: Step
    success: bool
    result: Any = None
    error: str = None
    duration_ms: int = 0
    attempt: int = 1
    adapted: bool = False  # True if fallback was used

@dataclass
class PlanResult:
    """Result of executing a full plan."""
    success: bool
    steps_completed: int
    total_steps: int
    step_results: List[StepResult]
    context: str
    started_at: float
    finished_at: float
    adaptations: List[str] = field(default_factory=list)

def _resolve_args(args: dict, previous_results: List[StepResult]) -> dict:
    """Resolve template references in args like {step0.result.url}."""
    resolved = {}
    
    for key, value in args.items():
        if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
            # Template reference
            ref = value[1:-1]  # Remove braces
            parts = ref.split(".")
            
            if parts[0].startswith("step"):
                step_idx = int(parts[0].replace("step", ""))
                if step_idx < len(previous_results):
                    step_result = previous_results[step_idx]
                    
                    # Navigate through result object
                    current = step_result.result
                    for part in parts[1:]:
                        if isinstance(current, dict):
                            current = current.get(part)
                        elif hasattr(current, part):
                            current = getattr(current, part)
                        else:
                            current = None
                            break
                    
                    resolved[key] = current
                else:
                    resolved[key] = None
            else:
                resolved[key] = value
        else:
            resolved[key] = value
    
    return resolved

def _execute_tool(tool_name: str, args: dict) -> Any:
    """Execute a tool by name. This is a placeholder - actual execution depends on Hermes runtime."""
    # In practice, this would call the actual Hermes tool dispatch
    # For now, return a mock result for testing
    return {"status": "mock", "tool": tool_name, "args": args}

def execute_step(step: Step, previous_results: List[StepResult], 
                 attempt: int = 1) -> StepResult:
    """Execute a single step with retry logic."""
    start = time.time()
    
    # Check condition
    if step.condition:
        # Evaluate condition against previous results
        # Simplified: condition is a key that must exist in last result
        if previous_results and not _check_condition(step.condition, previous_results[-1]):
            return StepResult(
                step=step,
                success=True,
                result={"skipped": True, "reason": f"condition not met: {step.condition}"},
                duration_ms=0,
                attempt=attempt
            )
    
    # Resolve template args
    resolved_args = _resolve_args(step.args, previous_results)
    
    # Try primary tool
    try:
        result = _execute_tool(step.tool, resolved_args)
        duration = int((time.time() - start) * 1000)
        
        if TOOL_LOGGER:
            log_tool_call(step.tool, resolved_args, result, success=True, 
                         duration_ms=duration, context="plan_executor")
        
        return StepResult(
            step=step,
            success=True,
            result=result,
            duration_ms=duration,
            attempt=attempt
        )
    
    except Exception as e:
        error = str(e)
        duration = int((time.time() - start) * 1000)
        
        if TOOL_LOGGER:
            log_tool_call(step.tool, resolved_args, None, success=False,
                         error=error, duration_ms=duration, context="plan_executor")
        
        # Retry if attempts remain
        if attempt < step.retries:
            time.sleep(1)  # Brief pause before retry
            return execute_step(step, previous_results, attempt + 1)
        
        # Try fallback if available
        if step.fallback_tool:
            try:
                result = _execute_tool(step.fallback_tool, resolved_args)
                duration = int((time.time() - start) * 1000)
                
                if TOOL_LOGGER:
                    log_tool_call(step.fallback_tool, resolved_args, result, 
                                 success=True, duration_ms=duration, context="plan_executor_fallback")
                
                return StepResult(
                    step=step,
                    success=True,
                    result=result,
                    duration_ms=duration,
                    attempt=attempt,
                    adapted=True
                )
            except Exception as fallback_error:
                error = f"Primary: {error} | Fallback: {str(fallback_error)}"
        
        return StepResult(
            step=step,
            success=False,
            error=error,
            duration_ms=duration,
            attempt=attempt
        )

def _check_condition(condition: str, last_result: StepResult) -> bool:
    """Check if a condition is met based on last result."""
    if not last_result or not last_result.result:
        return False
    
    # Simple conditions: key exists, value equals, etc.
    if condition.startswith("has:"):
        key = condition[4:]
        return isinstance(last_result.result, dict) and key in last_result.result
    
    if condition.startswith("success"):
        return last_result.success
    
    return True

def execute_plan(steps: List[Step], context: str = "", 
                 continue_on_error: bool = False) -> PlanResult:
    """Execute a multi-step plan with full retry and adaptation."""
    started_at = time.time()
    step_results = []
    adaptations = []
    
    print(f"[PLAN] Starting plan with {len(steps)} steps")
    print(f"[PLAN] Context: {context or 'none'}")
    
    for i, step in enumerate(steps):
        print(f"\n[PLAN] Step {i+1}/{len(steps)}: {step.description}")
        
        result = execute_step(step, step_results)
        step_results.append(result)
        
        if result.adapted:
            adaptations.append(f"Step {i+1}: used fallback {step.fallback_tool}")
            print(f"[PLAN] Adapted: used fallback {step.fallback_tool}")
        
        if result.success:
            print(f"[PLAN] ✓ Success ({result.duration_ms}ms, attempt {result.attempt})")
        else:
            print(f"[PLAN] ✗ Failed: {result.error}")
            if not continue_on_error:
                print(f"[PLAN] Aborting plan")
                break
    
    finished_at = time.time()
    steps_completed = sum(1 for r in step_results if r.success)
    
    plan_result = PlanResult(
        success=steps_completed == len(steps),
        steps_completed=steps_completed,
        total_steps=len(steps),
        step_results=step_results,
        context=context,
        started_at=started_at,
        finished_at=finished_at,
        adaptations=adaptations
    )
    
    # Log plan execution
    _log_plan_execution(plan_result)
    
    print(f"\n[PLAN] Completed: {steps_completed}/{len(steps)} steps successful")
    print(f"[PLAN] Duration: {finished_at - started_at:.1f}s")
    
    return plan_result

def _log_plan_execution(result: PlanResult):
    """Log plan execution to file for analysis."""
    log_file = Path.home() / ".hermes" / "plan_executions.jsonl"
    
    log_entry = {
        "timestamp": time.time(),
        "context": result.context,
        "total_steps": result.total_steps,
        "steps_completed": result.steps_completed,
        "success": result.success,
        "duration_seconds": result.finished_at - result.started_at,
        "adaptations": result.adaptations,
        "step_tools": [r.step.tool for r in result.step_results],
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry, default=str) + "\n")

def get_plan_stats(time_window_hours: int = 168):
    """Get statistics on plan executions."""
    log_file = Path.home() / ".hermes" / "plan_executions.jsonl"
    
    if not log_file.exists():
        return {"total_plans": 0}
    
    since = time.time() - (time_window_hours * 3600)
    plans = []
    
    with open(log_file) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry['timestamp'] > since:
                    plans.append(entry)
            except:
                pass
    
    if not plans:
        return {"total_plans": 0}
    
    successful = sum(1 for p in plans if p['success'])
    
    return {
        "total_plans": len(plans),
        "successful": successful,
        "success_rate": successful / len(plans),
        "avg_steps": sum(p['total_steps'] for p in plans) / len(plans),
        "avg_duration": sum(p['duration_seconds'] for p in plans) / len(plans),
        "total_adaptations": sum(len(p.get('adaptations', [])) for p in plans),
    }

if __name__ == "__main__":
    print("=== Plan Executor Test ===")
    
    # Test plan
    plan = [
        Step(tool="web_search", args={"query": "AI agents"}, retries=1),
        Step(tool="web_extract", args={"url": "https://example.com"}, retries=1, 
             fallback_tool="browser_navigate"),
    ]
    
    result = execute_plan(plan, context="test run", continue_on_error=True)
    
    print(f"\nPlan success: {result.success}")
    print(f"Steps: {result.steps_completed}/{result.total_steps}")
    
    print("\n=== Plan Executor Ready ===")
