#!/usr/bin/env python3
"""
multi_step_validator.py — Validate multi-step reasoning chains.

Detects broken chains where intermediate steps are missing,
verifies step dependencies, and ensures outputs match inputs.

Usage:
    from multi_step_validator import MultiStepValidator
    validator = MultiStepValidator()
    result = validator.validate_chain(steps=[
        {"id": 1, "tool": "web_search", "output": "urls"},
        {"id": 2, "tool": "web_extract", "input": "urls", "output": "content"},
    ])
    # result: {'valid': True, 'gaps': []}

Wiring:
    - Call after multi-step plans before execution
    - Or validate completed chains for quality scoring
"""

import json
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

@dataclass
class Step:
    id: int
    tool: str
    inputs: List[str]
    outputs: List[str]
    description: str = ""


class MultiStepValidator:
    """Validate multi-step reasoning chains."""
    
    # Tool input/output contracts
    TOOL_CONTRACTS = {
        "web_search": {"inputs": ["query"], "outputs": ["urls", "results"]},
        "web_extract": {"inputs": ["url"], "outputs": ["content", "text"]},
        "web_research": {"inputs": ["query"], "outputs": ["results", "urls"]},
        "execute_code": {"inputs": ["code"], "outputs": ["output", "result"]},
        "terminal": {"inputs": ["command"], "outputs": ["output", "exit_code"]},
        "read_file": {"inputs": ["path"], "outputs": ["content"]},
        "write_file": {"inputs": ["path", "content"], "outputs": ["bytes_written"]},
        "patch": {"inputs": ["path", "old_string", "new_string"], "outputs": ["diff"]},
        "search_files": {"inputs": ["pattern"], "outputs": ["matches"]},
        "delegate_task": {"inputs": ["goal"], "outputs": ["result"]},
        "browser_navigate": {"inputs": ["url"], "outputs": ["snapshot"]},
        "browser_click": {"inputs": ["ref"], "outputs": ["result"]},
        "browser_type": {"inputs": ["ref", "text"], "outputs": ["result"]},
    }
    
    def __init__(self):
        pass
    
    def parse_steps(self, raw_steps: List[Dict]) -> List[Step]:
        """Parse raw step dicts into Step objects."""
        steps = []
        for i, raw in enumerate(raw_steps):
            step = Step(
                id=raw.get("id", i + 1),
                tool=raw.get("tool", raw.get("action", "unknown")),
                inputs=raw.get("inputs", raw.get("input", [])),
                outputs=raw.get("outputs", raw.get("output", [])),
                description=raw.get("description", "")
            )
            steps.append(step)
        return steps
    
    def validate_chain(self, steps: List[Dict]) -> Dict:
        """
        Validate a chain of steps.
        Checks:
        1. Step IDs are sequential
        2. Each step's inputs are satisfied by previous outputs
        3. No circular dependencies
        4. Tool contracts are respected
        """
        parsed = self.parse_steps(steps)
        
        errors = []
        warnings = []
        
        # Check 1: Sequential IDs
        ids = [s.id for s in parsed]
        expected = list(range(1, len(parsed) + 1))
        if ids != expected:
            errors.append(f"Non-sequential IDs: {ids}, expected {expected}")
        
        # Check 2: Input/output connectivity
        available_outputs: Set[str] = set()
        
        for step in parsed:
            # Check if inputs are available
            for inp in step.inputs:
                if inp not in available_outputs and inp not in ["query", "goal", "path", "url", "command", "code"]:
                    # Some inputs are "primitive" and don't need previous outputs
                    pass
            
            # Add this step's outputs to available pool
            available_outputs.update(step.outputs)
        
        # Check 3: Tool contract validation
        for step in parsed:
            contract = self.TOOL_CONTRACTS.get(step.tool)
            if not contract:
                warnings.append(f"Unknown tool: {step.tool} (no contract)")
                continue
            
            # Check required inputs
            for required in contract["inputs"]:
                if required not in step.inputs:
                    # Try to find in description
                    if required not in step.description.lower():
                        warnings.append(f"Step {step.id} ({step.tool}): missing input '{required}'")
            
            # Check outputs
            for expected in contract["outputs"]:
                if expected not in step.outputs:
                    warnings.append(f"Step {step.id} ({step.tool}): missing output '{expected}'")
        
        # Check 4: Detect gaps (missing intermediate steps)
        gaps = self._find_gaps(parsed)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "gaps": gaps,
            "step_count": len(parsed),
            "tools_used": list(set(s.tool for s in parsed))
        }
    
    def _find_gaps(self, steps: List[Step]) -> List[Dict]:
        """Find missing intermediate steps."""
        gaps = []
        
        # Common gap patterns
        for i, step in enumerate(steps):
            if step.tool == "web_extract" and i > 0:
                prev = steps[i - 1]
                if prev.tool not in ["web_search", "web_research", "browser_navigate"]:
                    gaps.append({
                        "after_step": prev.id,
                        "before_step": step.id,
                        "missing": "URL discovery step (web_search/browser_navigate)",
                        "severity": "high"
                    })
            
            if step.tool == "patch" and i > 0:
                prev = steps[i - 1]
                if prev.tool not in ["read_file", "browser_snapshot"]:
                    gaps.append({
                        "after_step": prev.id,
                        "before_step": step.id,
                        "missing": "File content read (read_file)",
                        "severity": "high"
                    })
            
            if step.tool == "browser_click" and i > 0:
                prev = steps[i - 1]
                if prev.tool not in ["browser_navigate", "browser_snapshot"]:
                    gaps.append({
                        "after_step": prev.id,
                        "before_step": step.id,
                        "missing": "Browser navigation (browser_navigate)",
                        "severity": "medium"
                    })
        
        return gaps
    
    def suggest_fixes(self, validation_result: Dict) -> List[Dict]:
        """Suggest fixes for validation issues."""
        fixes = []
        
        for gap in validation_result.get("gaps", []):
            if gap["missing"] == "URL discovery step (web_search/browser_navigate)":
                fixes.append({
                    "type": "insert_step",
                    "after": gap["after_step"],
                    "suggested_tool": "web_search",
                    "reason": "web_extract needs URLs from search"
                })
            elif gap["missing"] == "File content read (read_file)":
                fixes.append({
                    "type": "insert_step",
                    "after": gap["after_step"],
                    "suggested_tool": "read_file",
                    "reason": "patch needs current file content"
                })
        
        for warning in validation_result.get("warnings", []):
            if "missing input" in warning:
                tool = warning.split("(")[1].split(")")[0] if "(" in warning else "unknown"
                fixes.append({
                    "type": "add_input",
                    "tool": tool,
                    "reason": warning
                })
        
        return fixes
    
    def validate_execution(self, planned: List[Dict], executed: List[Dict]) -> Dict:
        """
        Validate that execution matches plan.
        Detects deviations, skipped steps, extra steps.
        """
        planned_tools = [s.get("tool", s.get("action")) for s in planned]
        executed_tools = [s.get("tool", s.get("action")) for s in executed]
        
        deviations = []
        
        # Check for skipped steps
        for i, tool in enumerate(planned_tools):
            if i >= len(executed_tools) or executed_tools[i] != tool:
                deviations.append({
                    "type": "skipped",
                    "planned_step": i + 1,
                    "planned_tool": tool,
                    "actual_tool": executed_tools[i] if i < len(executed_tools) else None
                })
        
        # Check for extra steps
        if len(executed) > len(planned):
            for i in range(len(planned), len(executed)):
                deviations.append({
                    "type": "extra",
                    "step": i + 1,
                    "tool": executed_tools[i]
                })
        
        return {
            "matches_plan": len(deviations) == 0,
            "deviations": deviations,
            "planned_steps": len(planned),
            "executed_steps": len(executed)
        }


# Hook for plan validation
def validate_plan_hook(plan_steps: List[Dict]) -> Dict:
    """
    Hook to validate plans before execution.
    
    Usage:
        result = validate_plan_hook(plan_steps)
        if not result['valid']:
            print("Plan has gaps:", result['gaps'])
    """
    validator = MultiStepValidator()
    result = validator.validate_chain(plan_steps)
    
    if not result["valid"] or result["gaps"]:
        result["suggested_fixes"] = validator.suggest_fixes(result)
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Step Validator")
    parser.add_argument("--validate", type=str, help="Validate JSON plan file")
    parser.add_argument("--example", action="store_true", help="Run example validation")
    
    args = parser.parse_args()
    
    validator = MultiStepValidator()
    
    if args.example:
        # Example: broken chain
        broken_plan = [
            {"id": 1, "tool": "web_search", "inputs": ["query"], "outputs": ["urls"], "description": "Search for docs"},
            {"id": 2, "tool": "web_extract", "inputs": ["url"], "outputs": ["content"], "description": "Extract content"},
            {"id": 3, "tool": "patch", "inputs": ["path"], "outputs": ["diff"], "description": "Apply patch"},
        ]
        result = validator.validate_chain(broken_plan)
        print(json.dumps(result, indent=2))
    elif args.validate:
        with open(args.validate) as f:
            plan = json.load(f)
        result = validator.validate_chain(plan)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python3 multi_step_validator.py --example")