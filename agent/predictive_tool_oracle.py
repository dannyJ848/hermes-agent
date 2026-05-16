#!/usr/bin/env python3
"""
Predictive Tool Oracle — v1.0
═══════════════════════════════════════════════════════════════════════════════
Predicts which tools will be needed BEFORE the model asks for them.

PROBLEM: The model wastes turns discovering what tools exist and which to use.
Each "let me check what tools are available" turn costs tokens and time.

SOLUTION: Analyze the user's query and pre-load the most likely tools,
pre-fetch relevant data, and warm up tool caches.

PREDICTION SIGNALS:
  • Query keywords → tool mappings (learned from history)
  • Conversation phase → tool likelihood (research phase needs web_search)
  • File context → tool pre-loading (editing Python? pre-load patch, terminal)
  • Error patterns → recovery tools (previous error? pre-load fix tools)

INTEGRATION: Called in run_agent.py at conversation start and after each turn.
Pre-warms tool registry and caches likely results.

Author: Hermes Agent (self-improving)
Date: 2026-05-13
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


class ToolPredictionModel:
    """
    Learns query→tool mappings from historical usage.
    
    Uses a simple but effective approach:
    1. Tokenize queries into keywords
    2. Track which tools follow which keywords
    3. Use Bayesian scoring to predict likelihood
    """
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._keyword_tool_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._tool_success_rates: Dict[str, float] = {}
        self._session_tools_used: Set[str] = set()
        self._load_model()
    
    def _load_model(self):
        """Load historical tool usage patterns from database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            
            # Load keyword→tool mappings
            cursor = conn.execute(
                "SELECT query_keywords, tool_name, success FROM tool_predictions "
                "WHERE created_at > datetime('now', '-30 days')"
            )
            for row in cursor.fetchall():
                keywords = json.loads(row["query_keywords"])
                tool = row["tool_name"]
                success = row["success"]
                for kw in keywords:
                    self._keyword_tool_counts[kw][tool] += 1
                    if success:
                        self._keyword_tool_counts[kw][tool + "_success"] += 1
            
            # Load tool success rates
            cursor = conn.execute(
                "SELECT tool_name, AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as rate "
                "FROM tool_predictions GROUP BY tool_name"
            )
            for row in cursor.fetchall():
                self._tool_success_rates[row["tool_name"]] = row["rate"]
            
            conn.close()
        except Exception as e:
            logger.debug("Tool prediction model load failed: %s", e)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract predictive keywords from query."""
        # Normalize
        text = text.lower()
        
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        
        # Extract meaningful words
        words = re.findall(r"\b[a-z]{3,}\b", text)
        
        # Filter out stop words
        stop_words = {
            "the", "and", "for", "are", "but", "not", "you", "all", "can",
            "had", "her", "was", "one", "our", "out", "day", "get", "has",
            "him", "his", "how", "its", "may", "new", "now", "old", "see",
            "two", "way", "who", "boy", "did", "she", "use", "her", "now",
            "than", "them", "well", "were", "what", "with", "have", "from",
            "they", "know", "want", "been", "good", "much", "some", "time",
            "very", "when", "come", "here", "just", "like", "long", "make",
            "many", "over", "such", "take", "than", "them", "well", "were",
            "will", "would", "there", "could", "other", "after", "first",
            "never", "these", "think", "where", "being", "every", "great",
            "might", "shall", "still", "those", "while", "about", "before",
            "should", "through", "please", "could", "would", "should",
        }
        
        keywords = [w for w in words if w not in stop_words]
        
        # Add domain-specific bigrams
        bigrams = [f"{keywords[i]}_{keywords[i+1]}" for i in range(len(keywords)-1)]
        
        return keywords + bigrams
    
    def predict_tools(self, query: str, 
                      conversation_phase: str = "start",
                      available_tools: List[str] = None) -> List[Tuple[str, float]]:
        """
        Predict which tools will be needed.
        
        Returns:
            List of (tool_name, confidence_score) tuples, sorted by confidence.
        """
        keywords = self._extract_keywords(query)
        scores: Dict[str, float] = defaultdict(float)
        
        # Score based on keyword co-occurrence
        for kw in keywords:
            if kw in self._keyword_tool_counts:
                tool_counts = self._keyword_tool_counts[kw]
                total = sum(v for k, v in tool_counts.items() if not k.endswith("_success"))
                for tool, count in tool_counts.items():
                    if tool.endswith("_success"):
                        continue
                    # Bayesian scoring
                    success_count = tool_counts.get(tool + "_success", 0)
                    success_rate = self._tool_success_rates.get(tool, 0.5)
                    
                    # Higher score if keyword strongly predicts tool AND tool has high success
                    score = (count / max(total, 1)) * (0.5 + 0.5 * success_rate)
                    scores[tool] += score
        
        # Phase-based adjustments
        phase_boosts = {
            "start": {"web_search": 0.3, "web_extract": 0.2, "clarify": 0.1},
            "research": {"web_search": 0.5, "web_extract": 0.4, "delegate_task": 0.2},
            "coding": {"patch": 0.5, "terminal": 0.4, "write_file": 0.3, "read_file": 0.3},
            "debugging": {"terminal": 0.5, "read_file": 0.4, "search_files": 0.3},
            "review": {"read_file": 0.4, "search_files": 0.3, "delegate_task": 0.2},
            "deployment": {"terminal": 0.5, "delegate_task": 0.3, "verify_endpoint": 0.2},
        }
        
        for tool, boost in phase_boosts.get(conversation_phase, {}).items():
            scores[tool] += boost
        
        # Filter to available tools
        if available_tools:
            scores = {k: v for k, v in scores.items() if k in available_tools}
        
        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top predictions with confidence > 0.1
        return [(tool, score) for tool, score in sorted_scores if score > 0.1][:8]
    
    def record_prediction(self, query: str, predicted_tools: List[str], 
                          actual_tools: List[str], success: bool = True):
        """Record prediction outcome for learning."""
        try:
            keywords = self._extract_keywords(query)
            conn = sqlite3.connect(str(self.db_path))
            
            for tool in actual_tools:
                conn.execute(
                    "INSERT INTO tool_predictions (query_keywords, tool_name, predicted, success) "
                    "VALUES (?, ?, ?, ?)",
                    (json.dumps(keywords), tool, tool in predicted_tools, success)
                )
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug("Failed to record prediction: %s", e)
    
    def ensure_schema(self):
        """Create prediction tracking table."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_keywords TEXT,
                    tool_name TEXT,
                    predicted BOOLEAN,
                    success BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_pred_keywords 
                ON tool_predictions(query_keywords)
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass


class PredictiveToolOracle:
    """
    Main oracle interface. Predicts, pre-loads, and pre-fetches tool results.
    """
    
    def __init__(self):
        self.model = ToolPredictionModel()
        self.model.ensure_schema()
        self._preloaded_tools: Set[str] = set()
        self._prefetch_cache: Dict[str, Any] = {}
        self._conversation_phase = "start"
        self._turn_count = 0
    
    def predict_for_query(self, query: str, 
                          available_tools: List[str] = None) -> Dict[str, Any]:
        """
        Predict tools for a query and return pre-loading instructions.
        
        Returns:
            {
                "predicted_tools": [(name, confidence), ...],
                "preloaded": [tool names],
                "prefetch_suggestions": [what to pre-fetch],
                "phase": current conversation phase,
            }
        """
        self._turn_count += 1
        
        # Update phase based on turn count and query
        self._update_phase(query)
        
        # Get predictions
        predictions = self.model.predict_tools(
            query, self._conversation_phase, available_tools
        )
        
        # Determine what to preload
        preloaded = []
        prefetch_suggestions = []
        
        for tool, confidence in predictions:
            if confidence > 0.4 and tool not in self._preloaded_tools:
                preloaded.append(tool)
                self._preloaded_tools.add(tool)
        
        # Generate prefetch suggestions based on top predictions
        if predictions:
            top_tool = predictions[0][0]
            prefetch_suggestions = self._generate_prefetch_suggestions(top_tool, query)
        
        return {
            "predicted_tools": predictions,
            "preloaded": preloaded,
            "prefetch_suggestions": prefetch_suggestions,
            "phase": self._conversation_phase,
            "turn": self._turn_count,
        }
    
    def _update_phase(self, query: str):
        """Update conversation phase based on query and history."""
        query_lower = query.lower()
        
        # Phase detection
        if any(w in query_lower for w in ["debug", "error", "fix", "broken", "traceback"]):
            self._conversation_phase = "debugging"
        elif any(w in query_lower for w in ["search", "find", "research", "look up", "documentation"]):
            self._conversation_phase = "research"
        elif any(w in query_lower for w in ["code", "implement", "write", "function", "class"]):
            self._conversation_phase = "coding"
        elif any(w in query_lower for w in ["review", "audit", "check", "validate"]):
            self._conversation_phase = "review"
        elif any(w in query_lower for w in ["deploy", "release", "push", "build"]):
            self._conversation_phase = "deployment"
        elif self._turn_count > 5:
            # After 5 turns, likely in deep work
            self._conversation_phase = "deep_work"
    
    def _generate_prefetch_suggestions(self, tool: str, query: str) -> List[str]:
        """Generate suggestions for what to pre-fetch."""
        suggestions = []
        
        if tool == "web_search":
            # Extract search terms
            suggestions.append(f"Pre-search: '{query[:50]}...'")
        elif tool == "read_file":
            # Extract likely file paths
            file_patterns = re.findall(r"[\w\-./]+\.(py|js|ts|md|yaml|json|txt)\b", query)
            for fp in file_patterns[:3]:
                suggestions.append(f"Pre-read: {fp}")
        elif tool == "terminal":
            # Extract likely commands
            if "git" in query.lower():
                suggestions.append("Pre-check: git status")
            if "pip" in query.lower() or "install" in query.lower():
                suggestions.append("Pre-check: pip list")
        elif tool == "patch":
            suggestions.append("Pre-load: file contents for patching")
        
        return suggestions
    
    def record_actual_usage(self, query: str, tools_used: List[str], 
                            success: bool = True):
        """Record what tools were actually used for learning."""
        predicted = [t for t, _ in self.model.predict_tools(query)]
        self.model.record_prediction(query, predicted, tools_used, success)
    
    def get_tool_priority(self, tool_name: str) -> float:
        """Get priority score for a tool (for registry ordering)."""
        # Higher priority = tool should be registered earlier
        base_priority = self._tool_priority_scores.get(tool_name, 0.5)
        
        # Boost if recently predicted
        if tool_name in self._preloaded_tools:
            base_priority += 0.2
        
        return min(base_priority, 1.0)
    
    _tool_priority_scores = {
        "memory": 0.9,        # Always high — memory is foundational
        "session_search": 0.85,
        "clarify": 0.8,
        "web_search": 0.75,
        "read_file": 0.75,
        "terminal": 0.7,
        "patch": 0.7,
        "write_file": 0.65,
        "delegate_task": 0.6,
        "search_files": 0.6,
        "web_extract": 0.55,
        "todo": 0.5,
        "schedule_add": 0.45,
        "cost_check": 0.4,
        "telegram_status": 0.35,
    }


# Singleton accessor
_oracle: Optional[PredictiveToolOracle] = None


def get_oracle() -> PredictiveToolOracle:
    """Get the singleton oracle instance."""
    global _oracle
    if _oracle is None:
        _oracle = PredictiveToolOracle()
    return _oracle
