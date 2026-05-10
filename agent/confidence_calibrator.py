#!/usr/bin/env python3
"""
R45 — Confidence Calibrator — normalized confidence + self-evaluation.
Key insight (arXiv 2603.06604): SFT yields well-calibrated confidence via MLE;
RL (PPO/GRPO) and DPO induce overconfidence via reward exploitation.
Self-evaluation: ask "Is this correct? Yes/No" and use normalized P(Yes).
Post-RL self-distillation restores calibration.
"""
import threading, time
from typing import Dict, List, Optional
_INSTANCES, _LOCK = {}, threading.Lock()

class ConfidenceCalibrator:
    def __init__(self, session_id="default"):
        self.session_id = session_id
        self._calibrations: List[dict] = []
        self._total_calls = 0
        self._overconfident_count = 0  # Confident but wrong
        self._underconfident_count = 0  # Unconfident but right
    
    def record_prediction(self, confidence: float, correct: bool, task_type: str = "") -> dict:
        """Record a prediction with confidence and correctness for calibration tracking."""
        self._total_calls += 1
        miscalibrated = False
        if confidence > 0.8 and not correct:
            self._overconfident_count += 1
            miscalibrated = True
        elif confidence < 0.3 and correct:
            self._underconfident_count += 1
            miscalibrated = True
        
        entry = {"confidence": confidence, "correct": correct, "task_type": task_type,
                 "miscalibrated": miscalibrated, "timestamp": time.time()}
        self._calibrations.append(entry)
        return {"miscalibrated": miscalibrated, "type": "overconfident" if confidence > 0.8 and not correct else
                "underconfident" if confidence < 0.3 and correct else "calibrated"}
    
    def compute_ece(self, n_bins: int = 10) -> float:
        """Expected Calibration Error: |acc - conf| weighted by bin size."""
        if not self._calibrations:
            return 0.0
        calibrations = sorted(self._calibrations, key=lambda x: x["confidence"])
        bin_size = max(1, len(calibrations) // n_bins)
        ece = 0.0
        for i in range(0, len(calibrations), bin_size):
            bin_entries = calibrations[i:i+bin_size]
            if bin_entries:
                avg_conf = sum(e["confidence"] for e in bin_entries) / len(bin_entries)
                avg_acc = sum(1 for e in bin_entries if e["correct"]) / len(bin_entries)
                ece += (len(bin_entries) / len(calibrations)) * abs(avg_acc - avg_conf)
        return round(ece, 3)
    
    def get_calibration_advice(self) -> Optional[str]:
        """Provide calibration advice based on miscalibration patterns."""
        if self._total_calls < 5:
            return None
        over_ratio = self._overconfident_count / max(1, self._total_calls)
        under_ratio = self._underconfident_count / max(1, self._total_calls)
        if over_ratio > 0.2:
            return "High overconfidence detected. Apply self-verification: re-evaluate answers before committing."
        elif under_ratio > 0.15:
            return "High underconfidence. Trust well-calibrated tool outputs more aggressively."
        return None
    
    def get_stats(self):
        ece = self.compute_ece()
        return {"total": self._total_calls, "overconfident": self._overconfident_count,
                "underconfident": self._underconfident_count, "ece": ece}
    
    def build_injection(self, context="") -> Optional[str]:
        advice = self.get_calibration_advice()
        if not advice:
            return None
        ece = self.compute_ece()
        return f"[CALIBRATION] ECE={ece:.3f}. {advice}"

def get_instance(session_id="default"):
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = ConfidenceCalibrator(session_id)
        return _INSTANCES[session_id]

if __name__ == "__main__":
    cc = ConfidenceCalibrator("test")
    cc.record_prediction(0.9, False)  # overconfident
    cc.record_prediction(0.2, True)   # underconfident
    cc.record_prediction(0.8, True)   # well-calibrated
    cc.record_prediction(0.5, False)  # well-calibrated
    cc.record_prediction(0.7, True)   # well-calibrated
    print(f"ECE: {cc.compute_ece()}")
    print(f"Advice: {cc.get_calibration_advice()}")
    print(f"Injection: {cc.build_injection()}")
    print("✓ OK")
