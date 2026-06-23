"""
Adaptive Context Injection System — Kimi Harness Enhancement

Replaces dumb "dump everything" injection with smart relevance-filtered injection.
Only injects memory entries and skills that match the current conversation context.

Key features:
- Relevance scoring: TF-IDF-style matching between user query and memory entries
- Skill filtering: Only show skills whose names/descriptions match current topic
- Budget enforcement: Hard cap on injection tokens with graceful degradation
- Dynamic trimming: When over budget, trim least-relevant entries first
- Query caching: Reuse scoring across turns when query hasn't changed much

Author: Kimi (via Hermes harness modification)
Date: 2026-04-26
"""

from __future__ import annotations

import json
import logging
import math
import re
import threading
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

# Optional heavy deps — imported once at module load (not per-call). These
# are gated in try/except so the module degrades gracefully to TF-IDF when
# sentence_transformers or numpy is absent. Hoisting here avoids ~850
# redundant sys.modules dict lookups per turn (score_relevance is called
# once per skill in the 425-entry index).
_SENTENCE_TRANSFORMERS = None
_NUMPY = None
try:
    import numpy as _np_mod  # noqa: F401
    _NUMPY = _np_mod
except Exception:
    pass
try:
    from sentence_transformers import SentenceTransformer as _STClass  # noqa: F401
    _SENTENCE_TRANSFORMERS = _STClass
except Exception:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_INJECTION_BUDGET_TOKENS = 8000  # Max tokens for ALL injected context
MEMORY_BUDGET_RATIO = 0.60  # 60% of budget goes to memory
SKILLS_BUDGET_RATIO = 0.25  # 25% goes to skills
RESERVE_BUDGET_RATIO = 0.15  # 15% reserve for identity/timestamp/etc

MIN_RELEVANCE_SCORE = 0.05  # Entries below this are dropped entirely
MAX_MEMORY_ENTRIES = 30  # Hard cap on memory entries per turn
MAX_SKILLS_SHOWN = 25  # Hard cap on skills shown per turn

# Stopwords for relevance scoring
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
    "because", "until", "while", "this", "that", "these", "those", "i",
    "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "whose", "s",
    "t", "don", "doesn", "didn", "wasn", "weren", "haven", "hasn", "hadn",
    "won", "wouldn", "shouldn", "isn", "aren", "ain", "couldn", "mightn",
    "mustn", "needn", "shan", "daren", "oughtn", "usedn", "ll", "re", "ve",
    "d", "m", "o", "y", "ma", "also", "get", "use", "using", "one", "two",
    "way", "make", "made", "go", "going", "went", "gone", "see", "seen",
    "saw", "know", "knew", "known", "think", "thought", "say", "said",
    "take", "took", "taken", "come", "came", "want", "wanted", "look",
    "looked", "find", "found", "give", "gave", "given", "tell", "told",
    "work", "worked", "feel", "felt", "try", "tried", "leave", "left",
    "call", "called", "good", "new", "first", "last", "long", "great",
    "little", "own", "other", "old", "right", "big", "high", "different",
    "small", "large", "next", "early", "young", "important", "few",
    "public", "bad", "same", "able", "hermes", "tool", "tools", "skill",
    "skills", "file", "files", "code", "python", "run", "running", "set",
    "up", "down", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "now", "today", "yesterday", "tomorrow", "time", "date", "day", "week",
    "month", "year", "hour", "minute", "second", "ago", "later", "soon",
    "still", "already", "yet", "even", "ever", "never", "always", "often",
    "sometimes", "usually", "rarely", "seldom", "maybe", "perhaps", "probably",
    "definitely", "certainly", "surely", "actually", "really", "truly",
    "exactly", "precisely", "specifically", "particularly", "especially",
    "mainly", "mostly", "generally", "usually", "normally", "typically",
    "basically", "essentially", "fundamentally", "primarily", "principally",
    "chiefly", "largely", "partly", "partially", "mostly", "almost",
    "nearly", "approximately", "roughly", "about", "around", "quite",
    "rather", "pretty", "fairly", "relatively", "comparatively", "extremely",
    "very", "too", "so", "enough", "quite", "rather", "pretty", "fairly",
    "relatively", "comparatively", "extremely", "very", "too", "so",
    "enough", "quite", "rather", "pretty", "fairly", "relatively",
    "comparatively", "extremely", "very", "too", "so", "enough",
}

# ---------------------------------------------------------------------------
# Token estimation — tiktoken-accurate with fast fallback
# ---------------------------------------------------------------------------

_tiktoken_encoder = None
_tiktoken_lock = threading.Lock()

def _get_encoder():
    """Lazy-load tiktoken encoder (thread-safe)."""
    global _tiktoken_encoder
    if _tiktoken_encoder is not None:
        return _tiktoken_encoder
    with _tiktoken_lock:
        if _tiktoken_encoder is not None:
            return _tiktoken_encoder
        try:
            import tiktoken
            _tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
            logger.info("tiktoken cl100k_base loaded for accurate token counting")
        except Exception as e:
            logger.warning(f"tiktoken unavailable ({e}), using fallback estimation")
            _tiktoken_encoder = False  # sentinel: tried and failed
    return _tiktoken_encoder

def estimate_tokens(text: str) -> int:
    """Accurate token count via tiktoken, fallback to ~4 chars/token."""
    if not text:
        return 0
    enc = _get_encoder()
    if enc is False:
        return max(1, len(text) // 4)
    try:
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Relevance scoring
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Extract meaningful tokens from text."""
    text = text.lower()
    # Split on non-alphanumeric, keep alphanumeric tokens 2+ chars
    tokens = re.findall(r'[a-z0-9]{2,}', text)
    # Filter stopwords and pure numbers
    return [t for t in tokens if t not in _STOPWORDS and not t.isdigit()]


def _build_tf_vector(tokens: List[str]) -> Counter:
    """Build term frequency vector."""
    return Counter(tokens)


def _cosine_similarity(vec1: Counter, vec2: Counter) -> float:
    """Compute cosine similarity between two TF vectors."""
    if not vec1 or not vec2:
        return 0.0
    
    # Get all unique terms
    all_terms = set(vec1.keys()) | set(vec2.keys())
    
    # Compute dot product and magnitudes
    dot_product = sum(vec1.get(t, 0) * vec2.get(t, 0) for t in all_terms)
    mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


def score_relevance(query: str, candidate: str) -> float:
    """
    Score how relevant `candidate` is to `query`.

    Uses semantic embeddings (sentence-transformers) when available,
    falls back to TF-IDF cosine similarity.
    """
    # Empty inputs are never relevant — guard before embedding. Empty
    # strings embed as near-zero vectors whose normalized dot product is
    # numerically unstable (can return ~1.0 for two empty inputs, which
    # would make an empty query spuriously match every candidate).
    if not query or not candidate:
        return 0.0

    # Try semantic embeddings first
    try:
        if _SENTENCE_TRANSFORMERS is None or _NUMPY is None:
            raise ImportError("optional deps not available")
        np = _NUMPY

        # Lazy-load model (cached)
        if not hasattr(score_relevance, '_model'):
            # Use lightweight model: 22MB, fast inference
            score_relevance._model = _SENTENCE_TRANSFORMERS('all-MiniLM-L6-v2')
            score_relevance._cache = {}  # Embedding cache
        
        model = score_relevance._model
        cache = score_relevance._cache
        
        # Get embeddings (cached)
        if query not in cache:
            cache[query] = model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        if candidate not in cache:
            cache[candidate] = model.encode(candidate, convert_to_numpy=True, normalize_embeddings=True)
        
        q_emb = cache[query]
        c_emb = cache[candidate]
        
        # Cosine similarity (already normalized)
        score = float(np.dot(q_emb, c_emb))
        return max(0.0, score)  # Clip negative values
        
    except Exception:
        # Fall back to TF-IDF
        pass
    
    # TF-IDF fallback
    q_tokens = set(_tokenize(query))
    c_tokens = set(_tokenize(candidate))
    
    if not q_tokens or not c_tokens:
        return 0.0
    
    # Cosine similarity approximation
    intersection = q_tokens & c_tokens
    if not intersection:
        return 0.0
    
    score = len(intersection) / (math.sqrt(len(q_tokens)) * math.sqrt(len(c_tokens)))
    return score


# ---------------------------------------------------------------------------
# Memory filtering
# ---------------------------------------------------------------------------

def filter_memory_entries(
    entries: List[str],
    query: str,
    budget_tokens: int,
    min_score: float = MIN_RELEVANCE_SCORE,
    max_entries: int = MAX_MEMORY_ENTRIES,
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Filter memory entries to only those relevant to the current query.
    Returns (filtered_entries, metadata).
    """
    if not entries or not query:
        return entries, {"total": len(entries), "kept": len(entries), "dropped": 0, "reason": "no_query"}
    
    # Score each entry
    # Hoist cortex_learning engine lookup out of the loop (same pattern as
    # filter_skills above).
    _cortex_engine = None
    try:
        from agent.cortex_learning import get_learning_engine as _gle
        _cortex_engine = _gle()
        if not hasattr(_cortex_engine, 'store'):
            _cortex_engine = None
    except Exception:
        _cortex_engine = None

    scored = []
    for entry in entries:
        score = score_relevance(query, entry)

        # Cortex learned score boost (engine resolved above the loop)
        if _cortex_engine is not None:
            try:
                entry_hash = str(hash(entry) % 10000000)
                stats = _cortex_engine.store.get_usage_stats(entry_hash)
                if stats and stats.get('found'):
                    learned_boost = (stats.get('effective_score', 0.5) - 0.5) * 0.3
                    score += learned_boost
            except Exception:
                pass

        scored.append((score, entry))
    
    # Sort by relevance descending
    scored.sort(key=lambda x: -x[0])
    
    # Take top entries within budget
    kept = []
    total_tokens = 0
    dropped = 0
    
    for score, entry in scored:
        if len(kept) >= max_entries:
            dropped += 1
            continue
        if score < min_score:
            dropped += 1
            continue
        
        entry_tokens = estimate_tokens(entry)
        if total_tokens + entry_tokens > budget_tokens:
            dropped += 1
            continue
        
        kept.append(entry)
        total_tokens += entry_tokens
    
    metadata = {
        "total": len(entries),
        "kept": len(kept),
        "dropped": dropped,
        "budget_tokens": budget_tokens,
        "used_tokens": total_tokens,
        "top_score": scored[0][0] if scored else 0,
        "min_score": min_score,
    }
    
    return kept, metadata


# ---------------------------------------------------------------------------
# Skills filtering
# ---------------------------------------------------------------------------

def warm_skill_embeddings(skills_by_category: Dict[str, List[Tuple[str, str]]]) -> int:
    """Batch-encode every skill candidate so filter_skills pays no per-call encode cost.

    The default score_relevance() path encodes each candidate lazily on first
    match. With 400+ skills that means ~400 sequential encode() calls on the
    first turn — visible latency. This warms the cache up front in a single
    batched model.encode() call (batch_size=64).

    Safe to call when sentence_transformers is unavailable or the model fails
    to load: returns 0 and score_relevance() will fall back to TF-IDF.

    Returns the number of candidates cached.
    """
    if not skills_by_category:
        return 0
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np  # noqa: F401  (consistency with score_relevance)

        # Lazy-load model (cached on the function attr, same singleton as score_relevance)
        if not hasattr(score_relevance, '_model'):
            score_relevance._model = SentenceTransformer('all-MiniLM-L6-v2')
            score_relevance._cache = {}
        model = score_relevance._model
        cache = score_relevance._cache

        # Collect every unique candidate text (name + description + category,
        # matching the text built inside filter_skills).
        seen: set[str] = set()
        to_encode: list[str] = []
        for category, skills in skills_by_category.items():
            for name, desc in skills:
                text = f"{name} {desc} {category}"
                if text and text not in seen and text not in cache:
                    seen.add(text)
                    to_encode.append(text)

        if not to_encode:
            return 0

        # Single batched encode pass — far cheaper than N individual calls.
        embs = model.encode(
            to_encode,
            batch_size=64,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        for text, emb in zip(to_encode, embs):
            cache[text] = emb
        return len(to_encode)
    except Exception as exc:
        # Networking failure, missing model, OOM, etc. — silently degrade.
        # score_relevance() will use the TF-IDF fallback for each candidate.
        logger.debug("warm_skill_embeddings failed, will use TF-IDF fallback: %s", exc)
        return 0


def filter_skills(
    skills_by_category: Dict[str, List[Tuple[str, str]]],
    query: str,
    budget_tokens: int,
    max_skills: int = MAX_SKILLS_SHOWN,
    min_score: float = MIN_RELEVANCE_SCORE,
) -> Tuple[Dict[str, List[Tuple[str, str]]], Dict[str, Any]]:
    """
    Filter skills to only those relevant to the current query.
    Returns (filtered_skills, metadata).
    """
    if not skills_by_category or not query:
        return skills_by_category, {"total": 0, "kept": 0, "dropped": 0, "reason": "no_query"}

    # Pre-warm embeddings in one batched pass so per-candidate score_relevance()
    # calls are just dict lookups + a dot product. Idempotent — the warm
    # function skips candidates already in the cache. No-op if the model
    # can't load (TF-IDF fallback handles scoring per-call).
    try:
        warm_skill_embeddings(skills_by_category)
    except Exception:
        pass

    # Score each skill
    # Hoist the cortex_learning engine lookup OUT of the per-skill loop —
    # get_learning_engine() constructs/returns a singleton, so calling it
    # 425×/turn is pure waste. Resolve once; skip the boost entirely if the
    # import or construction fails (graceful degradation).
    _cortex_engine = None
    try:
        from agent.cortex_learning import get_learning_engine as _gle
        _cortex_engine = _gle()
        if not hasattr(_cortex_engine, 'store'):
            _cortex_engine = None
    except Exception:
        _cortex_engine = None

    all_skills = []
    for category, skills in skills_by_category.items():
        for name, desc in skills:
            # Score based on name + description + category
            text = f"{name} {desc} {category}"
            score = score_relevance(query, text)

            # Cortex learned score boost (engine resolved above the loop)
            if _cortex_engine is not None:
                try:
                    stats = _cortex_engine.store.get_usage_stats(f"skill:{name}")
                    if stats and stats.get('found'):
                        learned_boost = (stats.get('effective_score', 0.5) - 0.5) * 0.3
                        score += learned_boost
                except Exception:
                    pass

            all_skills.append((score, category, name, desc))
    
    # Sort by relevance
    all_skills.sort(key=lambda x: -x[0])
    
    # Take top skills within budget
    kept_by_category: Dict[str, List[Tuple[str, str]]] = {}
    total_tokens = 0
    kept_count = 0
    dropped = 0
    
    for score, category, name, desc in all_skills:
        if kept_count >= max_skills:
            dropped += 1
            continue
        if score < min_score:
            dropped += 1
            continue
        
        skill_text = f"{name}: {desc}" if desc else name
        skill_tokens = estimate_tokens(skill_text)
        if total_tokens + skill_tokens > budget_tokens:
            dropped += 1
            continue
        
        kept_by_category.setdefault(category, []).append((name, desc))
        kept_count += 1
        total_tokens += skill_tokens
    
    # Sort categories and skills within categories
    sorted_result = {}
    for category in sorted(kept_by_category.keys()):
        sorted_result[category] = sorted(kept_by_category[category], key=lambda x: x[0])
    
    metadata = {
        "total": len(all_skills),
        "kept": kept_count,
        "dropped": dropped,
        "budget_tokens": budget_tokens,
        "used_tokens": total_tokens,
        "top_score": all_skills[0][0] if all_skills else 0,
        "min_score": min_score,
    }
    
    return sorted_result, metadata


# ---------------------------------------------------------------------------
# Budget tracking
# ---------------------------------------------------------------------------

class InjectionBudget:
    """Track injection token usage and enforce budgets."""
    
    def __init__(
        self,
        total_budget: int = DEFAULT_INJECTION_BUDGET_TOKENS,
        memory_ratio: float = MEMORY_BUDGET_RATIO,
        skills_ratio: float = SKILLS_BUDGET_RATIO,
    ):
        self.total_budget = total_budget
        self.memory_budget = int(total_budget * memory_ratio)
        self.skills_budget = int(total_budget * skills_ratio)
        self.reserve_budget = total_budget - self.memory_budget - self.skills_budget
        self.used = 0
        self.layers: Dict[str, int] = {}
        self.warnings: List[str] = []
    
    def allocate(self, layer_name: str, requested: int) -> int:
        """Allocate tokens for a layer. Returns actual allocated amount."""
        remaining = self.total_budget - self.used
        allocated = min(requested, remaining)
        self.layers[layer_name] = allocated
        self.used += allocated
        
        if allocated < requested:
            self.warnings.append(
                f"Layer '{layer_name}' truncated: requested {requested} tokens, "
                f"allocated {allocated} tokens (budget exhausted)"
            )
        
        return allocated
    
    @property
    def remaining_budget(self) -> int:
        """Tokens remaining in the injection budget."""
        return self.total_budget - self.used
    
    def report(self) -> Dict[str, Any]:
        """Generate budget usage report."""
        return {
            "total_budget": self.total_budget,
            "used": self.used,
            "remaining": self.remaining_budget,
            "utilization_pct": round(self.used / self.total_budget * 100, 1),
            "layers": self.layers,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Query context tracking (for caching)
# ---------------------------------------------------------------------------

class QueryContext:
    """Track the current conversation context for relevance scoring."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._last_query: str = ""
        self._last_scores: Dict[str, float] = {}
        self._last_turn: int = 0
        self._turn_count: int = 0
    
    def update(self, query: str) -> bool:
        """Update context. Returns True if query changed significantly."""
        with self._lock:
            self._turn_count += 1
            # Simple change detection: normalized query comparison
            normalized = " ".join(sorted(set(_tokenize(query))))
            if normalized == self._last_query:
                return False
            self._last_query = normalized
            self._last_scores = {}
            self._last_turn = self._turn_count
            return True
    
    def get_turn_count(self) -> int:
        with self._lock:
            return self._turn_count


# Global context tracker
_query_context = QueryContext()


def get_query_context() -> QueryContext:
    return _query_context


# ---------------------------------------------------------------------------
# Convenience: Build adaptive system prompt
# ---------------------------------------------------------------------------

def build_adaptive_memory_block(
    entries: List[str],
    query: str,
    budget_tokens: Optional[int] = None,
    pressure_level: str = "low",
) -> Tuple[str, Dict[str, Any]]:
    """
    Build a memory block with only relevant entries.
    Pressure-aware: reduces budget when context window is under pressure.
    Returns (block_text, metadata).
    """
    if budget_tokens is None:
        budget_tokens = int(DEFAULT_INJECTION_BUDGET_TOKENS * MEMORY_BUDGET_RATIO)
    
    # Adjust budget based on pressure
    if pressure_level == "critical":
        budget_tokens = int(budget_tokens * 0.3)  # 70% reduction
    elif pressure_level == "high":
        budget_tokens = int(budget_tokens * 0.5)  # 50% reduction
    elif pressure_level == "medium":
        budget_tokens = int(budget_tokens * 0.8)  # 20% reduction
    
    filtered, meta = filter_memory_entries(entries, query, budget_tokens)
    
    if not filtered:
        return "", meta
    
    content = "\n§\n".join(filtered)
    current = len(content)
    pct = min(100, int((current / (budget_tokens * 4)) * 100)) if budget_tokens > 0 else 0
    
    block = (
        "═" * 46 + "\n"
        f"MEMORY (your personal notes) [{pct}% — relevant entries only]\n"
        "═" * 46 + "\n"
        f"{content}\n"
        "═" * 46
    )
    
    meta["block_tokens"] = estimate_tokens(block)
    meta["pressure_level"] = pressure_level
    meta["adjusted_budget"] = budget_tokens
    return block, meta


def build_adaptive_skills_prompt(
    skills_by_category: Dict[str, List[Tuple[str, str]]],
    query: str,
    budget_tokens: Optional[int] = None,
    pressure_level: str = "low",
    max_skills: int = MAX_SKILLS_SHOWN,
    min_score: float = MIN_RELEVANCE_SCORE,
) -> Tuple[str, Dict[str, Any]]:
    """
    Build skills prompt with only relevant skills.
    Pressure-aware: reduces budget when context window is under pressure.
    Returns (prompt_text, metadata).

    ``max_skills`` and ``min_score`` override the module defaults so callers
    (e.g. config-driven injection) can tighten or loosen the filter without
    editing this module.
    """
    if budget_tokens is None:
        budget_tokens = int(DEFAULT_INJECTION_BUDGET_TOKENS * SKILLS_BUDGET_RATIO)

    # Adjust budget based on pressure
    if pressure_level == "critical":
        budget_tokens = int(budget_tokens * 0.3)
    elif pressure_level == "high":
        budget_tokens = int(budget_tokens * 0.5)
    elif pressure_level == "medium":
        budget_tokens = int(budget_tokens * 0.8)

    filtered, meta = filter_skills(
        skills_by_category, query, budget_tokens,
        max_skills=max_skills, min_score=min_score,
    )
    
    if not filtered:
        return "", meta
    
    index_lines = []
    for category in sorted(filtered.keys()):
        index_lines.append(f"  {category}:")
        for name, desc in filtered[category]:
            if desc:
                index_lines.append(f"    - {name}: {desc}")
            else:
                index_lines.append(f"    - {name}")
    
    result = (
        "## Skills (relevant to current context)\n"
        "Before replying, scan the skills below. If a skill matches or is even partially relevant "
        "to your task, you MUST load it with skill_view(name) and follow its instructions.\n"
        "\n"
        "<available_skills>\n"
        + "\n".join(index_lines) + "\n"
        "</available_skills>\n"
    )
    
    meta["block_tokens"] = estimate_tokens(result)
    meta["pressure_level"] = pressure_level
    meta["adjusted_budget"] = budget_tokens
    return result, meta
