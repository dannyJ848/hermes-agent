"""R220: Elo rating system - Elo rating for module quality."""
import threading
from typing import Dict, List

_INSTANCES: Dict[str, "EloRatingSystem"] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> "EloRatingSystem":
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = EloRatingSystem(session_id)
        return _INSTANCES[session_id]

class EloRatingSystem:
    K_FACTOR = 32
    BASE_RATING = 1500

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._injections = 0
        self._ratings = {}

    def build_injection(self, context: str = "") -> str:
        ctx = (context or "").lower()
        if not any(k in ctx for k in ["elo", "rating", "score", "rank", "compete"]):
            return ""
        self._injections += 1
        return "[ELO-RATING (1) each module starts at 1500, (2) K=32 for new modules, decay to 16 after 30 games, (3) match: compare module output vs expected, (4) winner gains, loser loses proportional to expected score, (5) top-rated modules get higher injection priority, (6) tournament every 300 calls]"

    def get_rating(self, module: str) -> float:
        return self._ratings.get(module, self.BASE_RATING)

    def update(self, winner: str, loser: str) -> Dict:
        r_a = self._ratings.get(winner, self.BASE_RATING)
        r_b = self._ratings.get(loser, self.BASE_RATING)
        
        e_a = 1.0 / (1.0 + 10**((r_b - r_a) / 400))
        e_b = 1.0 - e_a
        
        k_a = self.K_FACTOR if self._ratings.get(winner, 0) == 0 else 16
        k_b = self.K_FACTOR if self._ratings.get(loser, 0) == 0 else 16
        
        new_a = r_a + k_a * (1 - e_a)
        new_b = r_b + k_b * (0 - e_b)
        
        self._ratings[winner] = round(new_a, 1)
        self._ratings[loser] = round(new_b, 1)
        
        return {winner: round(new_a, 1), loser: round(new_b, 1)}

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        sorted_ratings = sorted(self._ratings.items(), key=lambda x: x[1], reverse=True)
        return [{"module": m, "rating": r} for m, r in sorted_ratings[:limit]]

    def get_status(self) -> Dict:
        return {"session": self.session_id, "injections": self._injections, "modules": len(self._ratings)}

