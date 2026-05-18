#!/usr/bin/env python3
"""
Adaptive Context Sculptor — v1.0
═══════════════════════════════════════════════════════════════════════════════
Dynamically optimizes context window allocation based on real-time task analysis.

PROBLEM: Static context compression wastes tokens on irrelevant history while
cutting critical information. One-size-fits-all compression harms complex tasks.

SOLUTION: Analyze the CURRENT task's complexity, then sculpt the context window:
  • Simple tasks (factual lookup): Aggressive compression, keep only recent turns
  • Medium tasks (code review): Moderate compression, preserve file context
  • Complex tasks (architecture design): Minimal compression, preserve reasoning chains
  • Crisis tasks (debugging): No compression, use full context + external memory

INTEGRATION: Hooked into run_agent.py before each model call. Replaces static
compression thresholds with dynamic, task-aware allocation.

Author: Hermes Agent (self-improving)
Date: 2026-05-13
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TaskProfile:
    """Real-time analysis of the current task's characteristics."""
    complexity_score: float  # 0.0-1.0
    reasoning_depth: int     # Estimated reasoning steps needed
    code_heavy: bool
    research_heavy: bool
    creative_heavy: bool
    debug_mode: bool
    multi_file: bool
    tool_intensive: bool
    urgency: str  # "low", "medium", "high", "critical"
    
    @property
    def context_priority(self) -> str:
        """Determine what type of context is most valuable."""
        if self.debug_mode:
            return "full_history"
        elif self.code_heavy and self.multi_file:
            return "file_context"
        elif self.research_heavy:
            return "accumulated_findings"
        elif self.creative_heavy:
            return "recent_turns"
        else:
            return "balanced"
    
    @property
    def compression_strategy(self) -> Dict[str, Any]:
        """Generate compression parameters based on task profile."""
        if self.complexity_score > 0.8 or self.debug_mode:
            # Minimal compression for complex/debug tasks
            return {
                "enabled": True,
                "threshold": 0.95,  # Only compress at 95% capacity
                "protect_first_n": 5,
                "protect_last_n": 10,
                "summary_ratio": 0.3,
                "preserve_reasoning": True,
                "preserve_code_blocks": True,
            }
        elif self.complexity_score > 0.5:
            # Moderate compression
            return {
                "enabled": True,
                "threshold": 0.85,
                "protect_first_n": 3,
                "protect_last_n": 6,
                "summary_ratio": 0.5,
                "preserve_reasoning": True,
                "preserve_code_blocks": True,
            }
        elif self.complexity_score > 0.3:
            # Standard compression
            return {
                "enabled": True,
                "threshold": 0.75,
                "protect_first_n": 3,
                "protect_last_n": 4,
                "summary_ratio": 0.6,
                "preserve_reasoning": False,
                "preserve_code_blocks": True,
            }
        else:
            # Aggressive compression for simple tasks
            return {
                "enabled": True,
                "threshold": 0.65,
                "protect_first_n": 2,
                "protect_last_n": 3,
                "summary_ratio": 0.8,
                "preserve_reasoning": False,
                "preserve_code_blocks": False,
            }


# ── UPSTREAM PATTERN: Feasibility Probes (adapted from conversation_compression.py) ──
# Before attempting compression, check if the auxiliary model can handle it.
# Warns when context window is too small; auto-lowers threshold when needed.

def check_compression_feasibility(agent):
    """Check if compression model can handle the task.
    
    Adapted from upstream check_compression_model_feasibility:
    - Probes auxiliary model context window
    - Compares against compression threshold
    - Auto-adjusts threshold if model is too small
    """
    if not getattr(agent, 'compression_enabled', False):
        return {"feasible": False, "reason": "compression_disabled"}
    
    try:
        # Get main model context length
        main_context = getattr(agent, 'context_length', 128000)
        
        # Get compression threshold (typically 80% of context)
        threshold = getattr(agent, 'compression_threshold', 0.8)
        needed = int(main_context * threshold)
        
        # Check if we have an auxiliary model configured
        aux_context = getattr(agent, 'aux_context_length', None)
        
        if aux_context is None:
            # Try to detect from config
            try:
                from agent.auxiliary_client import get_text_auxiliary_client
                client, aux_model = get_text_auxiliary_client("compression")
                if client and aux_model:
                    # Estimate context length from model name
                    if '4k' in aux_model.lower():
                        aux_context = 4096
                    elif '8k' in aux_model.lower():
                        aux_context = 8192
                    elif '16k' in aux_model.lower():
                        aux_context = 16384
                    elif '32k' in aux_model.lower():
                        aux_context = 32768
                    elif '128k' in aux_model.lower() or '200k' in aux_model.lower():
                        aux_context = 128000
                    else:
                        aux_context = 8192  # Default conservative
            except Exception:
                aux_context = 4096  # Conservative fallback
        
        if aux_context < needed:
            # Auto-lower threshold to fit
            new_threshold = (aux_context * 0.9) / main_context
            agent.compression_threshold = new_threshold
            return {
                "feasible": True,
                "warning": f"Aux model context ({aux_context}) < threshold ({needed}). Auto-lowered threshold to {new_threshold:.2%}",
                "aux_context": aux_context,
                "needed": needed,
                "adjusted_threshold": new_threshold
            }
        
        return {
            "feasible": True,
            "aux_context": aux_context,
            "needed": needed,
            "threshold": threshold
        }
        
    except Exception as e:
        return {"feasible": False, "reason": f"probe_error: {e}"}


def probe_before_compress(messages, agent):
    """Run feasibility probe before attempting compression."""
    feasibility = check_compression_feasibility(agent)
    
    if not feasibility.get("feasible"):
        logger.warning("Compression not feasible: %s", feasibility.get("reason"))
        return {"should_compress": False, "reason": feasibility.get("reason")}
    
    # Check message size
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    threshold_chars = getattr(agent, 'compression_threshold', 0.8) * getattr(agent, 'context_length', 128000)
    
    if total_chars < threshold_chars:
        return {"should_compress": False, "reason": "under_threshold", "total_chars": total_chars}
    
    if feasibility.get("warning"):
        logger.info(feasibility["warning"])
    
    return {
        "should_compress": True,
        "total_chars": total_chars,
        "threshold_chars": threshold_chars,
        "aux_context": feasibility.get("aux_context")
    }


# ── Original AdaptiveContextSculptor class continues below ──


class AdaptiveContextSculptor:
    """
    Analyzes conversation state and sculpts optimal context allocation.
    
    Usage:
        sculptor = AdaptiveContextSculptor()
        profile = sculptor.analyze_task(messages, current_query)
        strategy = profile.compression_strategy
        # Apply strategy to context compressor
    """
    
    # Complexity indicators
    COMPLEXITY_MARKERS = {
        "high": [
            r"\b(design|architect|refactor|restructure|migrate)\b",
            r"\b(debug|troubleshoot|diagnose|fix.*bug|root cause)\b",
            r"\b(compare.*contrast|evaluate.*options|trade-off|pros?\s+and\s+cons)\b",
            r"\b(implement.*feature|build.*system|create.*framework)\b",
            r"\b(integrate.*with|connect.*to|interface.*between)\b",
            r"\b(performance|optimize|scale|bottleneck|memory leak)\b",
            r"\b(security|vulnerability|exploit|sanitize|validate)\b",
        ],
        "medium": [
            r"\b(review|audit|check|verify|validate)\b",
            r"\b(update|modify|change|adjust|tweak)\b",
            r"\b(add|insert|append|extend)\b",
            r"\b(remove|delete|clean\s+up|prune)\b",
            r"\b(test|spec|assert|mock)\b",
            r"\b(document|explain|describe|clarify)\b",
        ],
        "code": [
            r"```[\w]*\n",  # Code blocks
            r"\b(function|class|def|import|from\s+\w+\s+import)\b",
            r"\b(API|endpoint|route|handler|middleware)\b",
            r"\b(database|query|SQL|schema|migration)\b",
        ],
        "research": [
            r"\b(research|find|search|look\s+up|investigate)\b",
            r"\b(latest|recent|new|update|version)\b",
            r"\b(documentation|docs|README|wiki)\b",
            r"\b(github|repo|repository|pull\s+request|issue)\b",
        ],
        "debug": [
            r"\b(error|exception|traceback|crash|fail)\b",
            r"\b(bug|broken|not\s+working|doesn't\s+work|won't)\b",
            r"\b(stack\s+trace|log|output|stderr)\b",
            r"\b(fix|solve|resolve|correct|repair)\b",
        ],
    }
    
    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        self._task_profiles: List[TaskProfile] = []
    
    def analyze_task(self, messages: List[Dict[str, str]], 
                     current_query: str = "") -> TaskProfile:
        """
        Analyze the current task and return a task profile.
        
        Args:
            messages: Full conversation history
            current_query: The latest user query
            
        Returns:
            TaskProfile with complexity analysis
        """
        # Combine recent messages for analysis
        recent_text = "\n".join([
            msg.get("content", "") for msg in messages[-5:]
            if msg.get("content")
        ])
        analysis_text = f"{current_query}\n{recent_text}".lower()
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity(analysis_text, messages)
        
        # Detect task characteristics
        code_heavy = self._detect_code_heavy(analysis_text)
        research_heavy = self._detect_research_heavy(analysis_text)
        creative_heavy = self._detect_creative_heavy(analysis_text)
        debug_mode = self._detect_debug_mode(analysis_text)
        multi_file = self._detect_multi_file(analysis_text)
        tool_intensive = self._detect_tool_intensive(messages)
        
        # Estimate reasoning depth
        reasoning_depth = self._estimate_reasoning_depth(analysis_text, messages)
        
        # Determine urgency
        urgency = self._detect_urgency(analysis_text)
        
        profile = TaskProfile(
            complexity_score=complexity_score,
            reasoning_depth=reasoning_depth,
            code_heavy=code_heavy,
            research_heavy=research_heavy,
            creative_heavy=creative_heavy,
            debug_mode=debug_mode,
            multi_file=multi_file,
            tool_intensive=tool_intensive,
            urgency=urgency,
        )
        
        self._task_profiles.append(profile)
        return profile
    
    def _calculate_complexity(self, text: str, messages: List[Dict[str, str]]) -> float:
        """Calculate complexity score 0.0-1.0."""
        score = 0.3  # Base complexity
        
        # Check for high-complexity markers
        for pattern in self.COMPLEXITY_MARKERS["high"]:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.15
        
        # Check for medium-complexity markers
        for pattern in self.COMPLEXITY_MARKERS["medium"]:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.05
        
        # Message count factor (longer conversations = more context needed)
        msg_factor = min(len(messages) / 20.0, 0.2)
        score += msg_factor
        
        # Code block factor
        code_blocks = len(re.findall(r"```[\w]*\n", text))
        score += min(code_blocks * 0.05, 0.15)
        
        return min(score, 1.0)
    
    def _detect_code_heavy(self, text: str) -> bool:
        """Detect if task is code-heavy."""
        code_markers = sum(
            1 for p in self.COMPLEXITY_MARKERS["code"]
            if re.search(p, text, re.IGNORECASE)
        )
        return code_markers >= 2
    
    def _detect_research_heavy(self, text: str) -> bool:
        """Detect if task requires research."""
        research_markers = sum(
            1 for p in self.COMPLEXITY_MARKERS["research"]
            if re.search(p, text, re.IGNORECASE)
        )
        return research_markers >= 2
    
    def _detect_creative_heavy(self, text: str) -> bool:
        """Detect if task is creative (writing, design, etc)."""
        creative_patterns = [
            r"\b(write|draft|create|generate|compose)\b",
            r"\b(design|style|theme|layout|visual)\b",
            r"\b(story|narrative|blog|article|essay)\b",
            r"\b(improve|enhance|polish|refine)\b",
        ]
        creative_markers = sum(
            1 for p in creative_patterns
            if re.search(p, text, re.IGNORECASE)
        )
        return creative_markers >= 2
    
    def _detect_debug_mode(self, text: str) -> bool:
        """Detect if we're in debugging mode."""
        debug_markers = sum(
            1 for p in self.COMPLEXITY_MARKERS["debug"]
            if re.search(p, text, re.IGNORECASE)
        )
        return debug_markers >= 2
    
    def _detect_multi_file(self, text: str) -> bool:
        """Detect if task involves multiple files."""
        file_patterns = [
            r"\b(files?|modules?|components?|packages?)\b",
            r"\b(import|from\s+\w+\s+import|require)\b",
            r"\b(across|between|multiple|several|all)\b",
        ]
        file_refs = len(re.findall(r"[\w\-./]+\.(py|js|ts|jsx|tsx|java|go|rs|cpp|c|h)\b", text))
        return file_refs >= 3 or sum(
            1 for p in file_patterns if re.search(p, text, re.IGNORECASE)
        ) >= 2
    
    def _detect_tool_intensive(self, messages: List[Dict[str, str]]) -> bool:
        """Detect if conversation is tool-intensive."""
        tool_calls = sum(
            1 for msg in messages
            if msg.get("role") == "assistant" and "tool_calls" in str(msg.get("content", ""))
        )
        return tool_calls >= 5
    
    def _estimate_reasoning_depth(self, text: str, messages: List[Dict[str, str]]) -> int:
        """Estimate required reasoning steps."""
        depth = 1
        
        # Question complexity
        question_count = text.count("?")
        depth += min(question_count, 3)
        
        # Conditional logic
        depth += len(re.findall(r"\b(if|when|unless|depending|based on)\b", text, re.IGNORECASE))
        
        # Comparison requirements
        depth += len(re.findall(r"\b(compare|versus|vs|difference|better|best)\b", text, re.IGNORECASE))
        
        # Step indicators
        step_indicators = len(re.findall(r"\b(step|phase|stage|part|section)\b", text, re.IGNORECASE))
        depth += min(step_indicators, 3)
        
        return min(depth, 10)
    
    def _detect_urgency(self, text: str) -> str:
        """Detect urgency level."""
        urgent_patterns = [
            r"\b(urgent|asap|immediately|critical|emergency|down|broken)\b",
            r"\b(blocking|stuck|can't|cannot|won't|failing)\b",
            r"\b(production|live|deploy|release|hotfix)\b",
        ]
        urgent_count = sum(
            1 for p in urgent_patterns if re.search(p, text, re.IGNORECASE)
        )
        
        if urgent_count >= 2:
            return "critical"
        elif urgent_count >= 1:
            return "high"
        elif re.search(r"\b(soon|today|tomorrow|deadline)\b", text, re.IGNORECASE):
            return "medium"
        else:
            return "low"
    
    def get_context_budget(self, profile: TaskProfile, 
                           total_tokens: int) -> Dict[str, int]:
        """
        Allocate context budget based on task profile.
        
        Returns token allocations for:
        - system_prompt: Fixed system instructions
        - recent_history: Most recent turns (always preserved)
        - working_memory: Task-specific context (files, research, etc)
        - long_term: Summarized older history
        """
        # Reserve tokens
        system_reserve = 2000
        available = total_tokens - system_reserve
        
        strategy = profile.compression_strategy
        
        if profile.debug_mode or profile.complexity_score > 0.8:
            # Prioritize full history
            recent_ratio = 0.6
            working_ratio = 0.3
            long_term_ratio = 0.1
        elif profile.code_heavy and profile.multi_file:
            # Prioritize file context
            recent_ratio = 0.4
            working_ratio = 0.45
            long_term_ratio = 0.15
        elif profile.research_heavy:
            # Prioritize accumulated findings
            recent_ratio = 0.35
            working_ratio = 0.5
            long_term_ratio = 0.15
        else:
            # Balanced
            recent_ratio = 0.5
            working_ratio = 0.3
            long_term_ratio = 0.2
        
        return {
            "system_prompt": system_reserve,
            "recent_history": int(available * recent_ratio),
            "working_memory": int(available * working_ratio),
            "long_term": int(available * long_term_ratio),
            "strategy": strategy,
        }
    
    def sculpt_context(self, messages: List[Dict[str, str]], 
                       system_prompt: str,
                       current_query: str,
                       max_tokens: int) -> Dict[str, Any]:
        """
        Main entry point: analyze task and return sculpted context.
        
        Returns:
            {
                "profile": TaskProfile,
                "budget": Dict[str, int],
                "recommendations": List[str],
                "compression_params": Dict[str, Any],
            }
        """
        profile = self.analyze_task(messages, current_query)
        budget = self.get_context_budget(profile, max_tokens)
        
        recommendations = []
        
        if profile.debug_mode:
            recommendations.append("🔍 DEBUG MODE: Preserve full error context and stack traces")
        if profile.code_heavy and profile.multi_file:
            recommendations.append("📁 MULTI-FILE: Preserve file relationships and cross-references")
        if profile.research_heavy:
            recommendations.append("🔬 RESEARCH MODE: Accumulate findings, minimize compression")
        if profile.urgency == "critical":
            recommendations.append("⚠️ CRITICAL: Fast path, minimal reasoning overhead")
        if profile.tool_intensive:
            recommendations.append("🛠️ TOOL-HEAVY: Preserve tool result context")
        
        return {
            "profile": profile,
            "budget": budget,
            "recommendations": recommendations,
            "compression_params": profile.compression_strategy,
        }


# Singleton accessor
_sculptor: Optional[AdaptiveContextSculptor] = None


def get_sculptor() -> AdaptiveContextSculptor:
    """Get the singleton sculptor instance."""
    global _sculptor
    if _sculptor is None:
        _sculptor = AdaptiveContextSculptor()
    return _sculptor
