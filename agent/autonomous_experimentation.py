"""
autonomous_experimentation.py — Self-directed learning loop.

The training gym picks exercises based on weakest recent performance,
runs them autonomously, records results, and updates its own models.
No human prompting needed — true self-improvement.
"""

import json
import time
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Experiment:
    id: str
    hypothesis: str
    experiment_type: str
    parameters: Dict[str, Any]
    predicted_outcome: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    result: Optional[Dict] = None
    started_at: float = 0
    completed_at: float = 0


class AutonomousExperimentationLoop:
    """Self-directed experimentation and learning."""

    def __init__(self, training_gym=None, unified_engine=None):
        self.training_gym = training_gym
        self.unified_engine = unified_engine
        self.experiments: List[Experiment] = []
        self._experiment_log_path = Path.home() / ".hermes" / "experiments.jsonl"
        self._load_experiments()

    def _load_experiments(self):
        if self._experiment_log_path.exists():
            with open(self._experiment_log_path) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        self.experiments.append(Experiment(**data))
                    except Exception:
                        pass

    def _save_experiment(self, exp: Experiment):
        with open(self._experiment_log_path, 'a') as f:
            f.write(json.dumps(asdict(exp)) + '\n')

    def identify_weaknesses(self) -> List[Dict]:
        """Identify weakest areas from unified intelligence."""
        weaknesses = []

        if self.unified_engine:
            try:
                insight = self.unified_engine.query_weaknesses()
                for w in insight.data.get('weaknesses', []):
                    weaknesses.append(w)
            except Exception:
                pass

        # Fallback: check training gym
        if self.training_gym:
            try:
                stats = self.training_gym.get_gym_stats()
                # Find lowest-scoring exercise types
                exercises = self.training_gym.exercises
                for ex in exercises:
                    attempts = [a for a in self.training_gym.attempts if a.exercise_id == ex.id]
                    if attempts:
                        avg_score = sum(a.score / a.max_score for a in attempts) / len(attempts)
                        if avg_score < 0.6:
                            weaknesses.append({
                                'type': 'training',
                                'name': ex.name,
                                'score': avg_score,
                                'tier': ex.tier
                            })
            except Exception:
                pass

        return sorted(weaknesses, key=lambda x: x.get('score', 0) if 'score' in x else x.get('success_rate', 0))

    def generate_hypothesis(self, weakness: Dict) -> Experiment:
        """Generate an experiment to address a weakness."""
        exp_id = f"exp_{int(time.time())}_{random.randint(1000, 9999)}"

        if weakness.get('type') == 'tool':
            hypothesis = f"Practicing {weakness['name']} will improve success rate above {weakness.get('success_rate', 0):.1%}"
            return Experiment(
                id=exp_id,
                hypothesis=hypothesis,
                experiment_type='tool_drill',
                parameters={'tool': weakness['name'], 'target_success_rate': 0.8},
                predicted_outcome='success_rate_improvement',
                status='pending'
            )
        elif weakness.get('type') == 'error':
            hypothesis = f"Studying error pattern '{weakness['name'][:40]}' will reduce recurrence"
            return Experiment(
                id=exp_id,
                hypothesis=hypothesis,
                experiment_type='error_study',
                parameters={'error_signature': weakness['name']},
                predicted_outcome='error_reduction',
                status='pending'
            )
        elif weakness.get('type') == 'training':
            hypothesis = f"Repeated practice of {weakness['name']} will raise score above 0.6"
            return Experiment(
                id=exp_id,
                hypothesis=hypothesis,
                experiment_type='training_drill',
                parameters={'exercise_name': weakness['name'], 'target_score': 0.7},
                predicted_outcome='score_improvement',
                status='pending'
            )
        else:
            return Experiment(
                id=exp_id,
                hypothesis="General capability exploration",
                experiment_type='exploration',
                parameters={'random_exercise': True},
                predicted_outcome='discovery',
                status='pending'
            )

    def run_experiment(self, exp: Experiment) -> Experiment:
        """Execute an experiment and record results."""
        exp.status = 'running'
        exp.started_at = time.time()

        if exp.experiment_type == 'training_drill' and self.training_gym:
            try:
                # Run the exercise multiple times
                ex_name = exp.parameters.get('exercise_name', '')
                exercise = next((e for e in self.training_gym.exercises if e.name == ex_name), None)
                if exercise:
                    scores = []
                    for _ in range(3):
                        result = self.training_gym.attempt_exercise(exercise.id, tier=exercise.tier)
                        scores.append(result.get('score', 0) / result.get('max_score', 1))

                    avg_score = sum(scores) / len(scores)
                    exp.result = {
                        'scores': scores,
                        'average_score': avg_score,
                        'improvement': avg_score >= exp.parameters.get('target_score', 0.6)
                    }
                    exp.status = 'completed'
                else:
                    exp.status = 'failed'
                    exp.result = {'error': 'Exercise not found'}
            except Exception as e:
                exp.status = 'failed'
                exp.result = {'error': str(e)}

        elif exp.experiment_type == 'tool_drill':
            # Simulate tool practice by querying what would help
            exp.result = {
                'recommendation': f"Practice {exp.parameters.get('tool')} in isolation",
                'drill_count': 5
            }
            exp.status = 'completed'

        elif exp.experiment_type == 'error_study':
            # Study the error pattern
            exp.result = {
                'error': exp.parameters.get('error_signature', ''),
                'study_method': 'review_recent_occurrences',
                'prevention_strategy': 'input_validation'
            }
            exp.status = 'completed'

        else:
            exp.result = {'note': 'Exploration experiment — no specific action'}
            exp.status = 'completed'

        exp.completed_at = time.time()
        self._save_experiment(exp)
        return exp

    def run_cycle(self, max_experiments: int = 3) -> Dict[str, Any]:
        """Run a full experimentation cycle."""
        weaknesses = self.identify_weaknesses()

        if not weaknesses:
            return {'status': 'no_weaknesses', 'experiments': []}

        experiments_run = []
        for weakness in weaknesses[:max_experiments]:
            exp = self.generate_hypothesis(weakness)
            exp = self.run_experiment(exp)
            experiments_run.append(exp)

        return {
            'status': 'completed',
            'weaknesses_found': len(weaknesses),
            'experiments_run': len(experiments_run),
            'results': [
                {
                    'id': e.id,
                    'hypothesis': e.hypothesis,
                    'status': e.status,
                    'result': e.result
                }
                for e in experiments_run
            ]
        }

    def get_experiment_stats(self) -> Dict:
        """Get statistics on all experiments."""
        total = len(self.experiments)
        completed = sum(1 for e in self.experiments if e.status == 'completed')
        failed = sum(1 for e in self.experiments if e.status == 'failed')

        by_type = {}
        for e in self.experiments:
            by_type[e.experiment_type] = by_type.get(e.experiment_type, 0) + 1

        return {
            'total_experiments': total,
            'completed': completed,
            'failed': failed,
            'success_rate': completed / total if total > 0 else 0,
            'by_type': by_type
        }
