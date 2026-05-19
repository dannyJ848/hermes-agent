"""Agent scorecard — lightweight performance evaluation."""

import time
from typing import Dict, Any, Optional


def compute_scorecard(
    session_count: Optional[int] = None,
    error_rate: Optional[float] = None,
    avg_duration: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute a lightweight agent performance scorecard.

    Parameters are optional — when None, the scorecard returns a template
    that the cognitive orchestrator can fill in later.
    """
    card: Dict[str, Any] = {
        "timestamp": time.time(),
        "overall_score": 0.0,
        "dimensions": {},
        "recommendations": [],
    }

    if session_count is not None:
        card["dimensions"]["experience_volume"] = min(session_count / 100.0, 1.0)

    if error_rate is not None:
        # Lower error rate = higher score
        card["dimensions"]["reliability"] = max(0.0, 1.0 - error_rate)

    if avg_duration is not None:
        # Faster responses = higher score (up to a point)
        card["dimensions"]["responsiveness"] = min(10.0 / max(avg_duration, 1.0), 1.0)

    # Compute overall score as mean of available dimensions
    dims = card["dimensions"]
    if dims:
        card["overall_score"] = sum(dims.values()) / len(dims)

    # Generate recommendations based on weakest dimension
    if dims:
        weakest = min(dims, key=dims.get)  # type: ignore[arg-type]
        if dims[weakest] < 0.5:
            card["recommendations"].append(f"Improve {weakest}: current score {dims[weakest]:.2f}")

    return card
