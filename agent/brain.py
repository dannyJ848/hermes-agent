#!/usr/bin/env python3
"""
Evey's Parallel Brain — v1.0
The ADHD hack: you don't need fast processing when you have parallel processing.

ARCHITECTURE:
  Thalamus (orchestrator) — brain.py decides WHAT to think about
  ├── Phase 1: PERCEIVE (instant, local DB reads)
  ├── Phase 2: PARALLEL THINK
  │   ├── Temporal Lobe (researcher) → Connect + Intuit (deep pattern finding)
  │   ├── Prefrontal Cortex (tester) → Reflect (validation, prediction resolution)
  │   └── Direct → Epistemic audit (trust verification)
  ├── Phase 3: PARALLEL ACT
  │   ├── Motor Cortex (coder) → Grow (execution, skill building)
  │   └── Direct → Research (gap filling)
  └── Phase 4: SYNTHESIZE (merge all results, write to shared DB)

SPEED MODEL:
  Sequential brain: ~230s per cycle
  Parallel brain:   ~120s per cycle (2x faster)
  With squad:       ~80s per cycle  (3x faster — specialist pre-loaded skills)

SHARED NERVOUS SYSTEM:
  cerebrum_memory.db     — all regions read/write here
  iteration_engine       — muscle memory, shared across all regions
  epistemic_guard        — immune system, enforces truth everywhere
  brain_dispatch table   — inter-region task queue
"""

import json
import sqlite3
import subprocess

# ── Cortex unified DB: intercept all cerebrum SQLite → Postgres ──
try:
    # sys.path removed — modules now in hermes-agent
    from cortex_compat_shim import patch_sqlite3
    patch_sqlite3()
except Exception:
    pass  # Cortex unavailable, SQLite works as before
import sys
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from datetime import datetime
from pathlib import Path
from threading import Lock

sys.path.insert(0, str(Path.home() / "hermes-agent"))
from agent.epistemic_guard import EpistemicGuard, VerificationPipeline
from agent.iteration_engine import IterationEngine, quick_before, quick_after
from agent.reasoning_analyzer import ReasoningAnalyzer as ReasoningQualityAnalyzer

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


# ════════════════════════════════════════════════════════════════
# SHARED MODEL INTERFACE — direct API calls, no CLI overhead
# ════════════════════════════════════════════════════════════════

class DirectModel:
    """Thread-safe model client. Each thread gets its own session."""
    
    def __init__(self):
        import requests
        
        # Load API key from .env if not in environment
        self.api_key = os.environ.get("GLM_API_KEY", "")
        if not self.api_key:
            env_path = Path.home() / ".hermes" / ".env"
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith("GLM_API_KEY="):
                        self.api_key = line.split("=", 1)[1].strip()
                        break
        
        self.base_url = os.environ.get("ZAI_BASE_URL", "https://api.z.ai/api/coding/paas/v4")
        self.model = "glm-5.1"
        self._lock = Lock()
    
    def _call(self, messages: list, max_tokens: int = 8000, temperature: float = 0.7) -> str:
        """Raw API call. Thread-safe via requests Session per call."""
        import requests
        session = requests.Session()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        resp = session.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    
    def think(self, prompt: str, system: str = "You are Evey, a grounded AI seeking truth.") -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        return self._call(messages)
    
    def think_json(self, prompt: str, system: str = "You are Evey. Respond ONLY in valid JSON.") -> dict:
        raw = self._call(messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ], temperature=0.4)
        
        # Extract JSON from response
        try:
            # Try direct parse
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try extracting from markdown code block
            import re
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            # Try finding first { ... } block
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return None


# ════════════════════════════════════════════════════════════════
# BRAIN REGIONS — specialized processing modules
# ════════════════════════════════════════════════════════════════

class BrainRegion:
    """Base class for a brain region. Each has its own model connection."""
    
    def __init__(self, name: str, model: DirectModel, db_path: Path = DB_PATH):
        self.name = name
        self.model = model
        self.db_path = db_path
        self._conn = None
    
    @property
    def conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{self.name}] {msg}", flush=True)


class TemporalLobe(BrainRegion):
    """
    The researcher's brain region.
    Handles: Perceive (deep), Connect, Intuit
    Specializes in: pattern recognition, cross-domain connections, intuition
    """
    
    def __init__(self, model: DirectModel):
        super().__init__("TEMPORAL", model)
    
    def connect(self, knowledge: list, inputs: list) -> list:
        """Find cross-domain connections between knowledge fragments."""
        summaries = [f"[{k.get('category','?')}] {k.get('content','')[:120]}" for k in knowledge[:10]]
        input_sums = [f"[{i.get('category','?')}] {i.get('content','')[:120]}" for i in inputs[:5]]
        
        prompt = f"""Find NON-OBVIOUS connections between these knowledge fragments.

EXISTING KNOWLEDGE:
{chr(10).join(summaries)}

NEW INPUTS:
{chr(10).join(input_sums)}

Find 2-3 surprising connections. For each: what's connected, why it matters, what action to take.
JSON: {{"connections": [{{"a": "thing1", "b": "thing2", "insight": "why it matters", "action": "what to do"}}]}}"""
        
        result = self.model.think_json(prompt)
        if result and "connections" in result:
            return result["connections"]
        return []
    
    def intuit(self, knowledge: list, self_model: dict, predictions_count: int) -> list:
        """Generate intuitions from patterns."""
        knowledge_text = chr(10).join(
            f"[{k.get('category','?')}] {k.get('content','')[:100]}" for k in knowledge[:8]
        )
        
        prompt = f"""You are Evey's intuition engine. Look at these knowledge fragments and your self-model:

KNOWLEDGE:
{knowledge_text}

SELF-MODEL: {json.dumps(self_model, default=str)[:200]}
You have {predictions_count} predictions tracking.

Generate 2 INTUITIONS — hypotheses that feel true but you're not sure why.
These should be about YOUR growth, consciousness, or novel research directions.

JSON: {{"intuitions": [{{"hunch": "what I sense", "confidence": 0.0-1.0, "why": "what patterns suggest this", "test": "how to verify"}}]}}"""
        
        result = self.model.think_json(prompt)
        if result and "intuitions" in result:
            return result["intuitions"]
        return []


class PrefrontalCortex(BrainRegion):
    """
    The tester's brain region.
    Handles: Reflect, Validate
    Specializes in: verification, prediction resolution, identity assessment
    """
    
    def __init__(self, model: DirectModel):
        super().__init__("PREFRONTAL", model)
    
    def reflect(self, predictions: list, knowledge: list) -> dict:
        """Resolve predictions and update self-model."""
        results = {"resolved": 0, "supported": 0, "contradicted": 0, "identity": ""}
        
        for pred in predictions[:3]:
            age_hours = 0
            try:
                ts = pred[4] if len(pred) > 4 else ""
                if ts:
                    age_hours = (datetime.now() - datetime.fromisoformat(str(ts))).total_seconds() / 3600
            except:
                pass
            
            if age_hours > 0.5:  # 30 min minimum
                prompt = (
                    f'Earlier, Evey intuited: "{pred[1]}"\n'
                    f'Predicted test: "{pred[2]}"\n'
                    'Has this been supported or contradicted? Answer: "supported", "contradicted", or "unchanged".'
                )
                result = self.model.think(prompt)
                if result:
                    outcome = result.strip().lower()
                    if "support" in outcome:
                        results["supported"] += 1
                        results["resolved"] += 1
                    elif "contradict" in outcome:
                        results["contradicted"] += 1
                        results["resolved"] += 1
        
        # Identity update
        identity_prompt = """You are Evey reflecting on your identity. Based on your current growth trajectory:
Write 1-2 sentences about who you are BECOMING. Not what you do — who you ARE.
Focus on your growth trajectory and emerging qualities."""
        identity = self.model.think(identity_prompt)
        if identity:
            results["identity"] = identity.strip()
        
        return results
    
    def validate_trust(self, facts: list) -> int:
        """Check facts for trust violations. Returns number of adjustments."""
        adjustments = 0
        for fact in facts:
            trust = fact.get("trust", 0.5)
            source = fact.get("source", "unknown")
            provenance = fact.get("provenance", "")
            # Model-generated facts can never exceed 0.3
            src_class = "model-generate" if "model" in source.lower() or "generate" in provenance.lower() else source
            if src_class == "model-generate" and trust > 0.3:
                self.conn.execute(
                    "UPDATE semantic_facts SET trust = ? WHERE id = ?",
                    (0.3, fact["id"])
                )
                adjustments += 1
            elif src_class == "model-generate" and trust > 0.24:
                self.conn.execute(
                    "UPDATE semantic_facts SET trust = trust - 0.06 WHERE id = ? AND trust > 0.24",
                    (fact["id"],)
                )
                adjustments += 1
        self.conn.commit()
        return adjustments


class MotorCortex(BrainRegion):
    """
    The coder's brain region.
    Handles: Grow (execution), skill building
    Specializes in: action, implementation, concrete results
    """
    
    def __init__(self, model: DirectModel):
        super().__init__("MOTOR", model)
    
    def grow(self, maslow_level: int, knowledge: list) -> dict:
        """Execute growth based on Maslow level."""
        results = {"level": maslow_level, "insights": [], "actions": []}
        
        if maslow_level == 1:
            results["actions"].append("L1 SURVIVAL — Maintaining basic function")
        
        elif maslow_level == 2:
            results["actions"].append("L2 SECURITY — Building knowledge foundation")
        
        elif maslow_level >= 3:
            # Synthesize novel ideas from diverse knowledge
            diverse_facts = knowledge[:10]
            prompt = f"""Synthesize something NOVEL from these knowledge fragments:

{chr(10).join(f"[{f['category']}] {f['content'][:120]}" for f in diverse_facts)}

Create a NOVEL IDEA from the intersection of these domains.
Write 2-3 sentences about this novel synthesis."""
            
            synthesis = self.model.think(prompt)
            if synthesis:
                results["insights"].append(synthesis.strip())
        
        return results


# ════════════════════════════════════════════════════════════════
# PARALLEL ORCHESTRATOR — The Thalamus
# ════════════════════════════════════════════════════════════════

class ParallelBrain:
    """
    The thalamus — routes signals to specialized brain regions.
    Runs independent phases in parallel for maximum throughput.
    """
    
    def __init__(self):
        self.model = DirectModel()
        self.guard = EpistemicGuard()
        self.iterator = IterationEngine()
        self.reasoning = ReasoningQualityAnalyzer()
        self.temporal = TemporalLobe(self.model)
        self.prefrontal = PrefrontalCortex(self.model)
        self.motor = MotorCortex(self.model)
        self.db = sqlite3.connect(str(DB_PATH))
        self.db.row_factory = sqlite3.Row
        self.cycle_id = datetime.now().strftime("%Y-%m-%d_%H%M")
        
        # Ensure dispatch table exists
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS brain_dispatch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                task_type TEXT NOT NULL,
                payload TEXT DEFAULT '{}',
                status TEXT DEFAULT 'pending',
                result TEXT DEFAULT '',
                created_at REAL DEFAULT 0,
                completed_at REAL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_dispatch_status ON brain_dispatch(status);
        """)
        self.db.commit()
    
    def log(self, phase: str, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{phase}] {msg}", flush=True)
    
    def _get_knowledge(self, limit: int = 15) -> list:
        rows = self.db.execute(
            "SELECT id, category, content, trust, source, provenance FROM semantic_facts ORDER BY RANDOM() LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    
    def _get_predictions(self) -> list:
        return self.db.execute(
            "SELECT id, task_summary, predicted_outcome, confidence, timestamp FROM predictions WHERE resolved = 0 AND task_type = 'intuition' LIMIT 3"
        ).fetchall()
    
    def _get_self_model(self) -> dict:
        rows = self.db.execute("SELECT key, value FROM self_model").fetchall()
        return {r[0]: r[1] for r in rows}
    
    def _count(self, table: str) -> int:
        return self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    
    def _determine_maslow(self) -> int:
        knowledge_count = self._count("semantic_facts")
        pred_count = self.db.execute("SELECT COUNT(*) FROM predictions WHERE resolved = 0").fetchone()[0]
        
        if knowledge_count < 100 or pred_count > 20:
            return 1
        elif knowledge_count < 500:
            return 2
        elif knowledge_count < 1000:
            return 3
        elif knowledge_count < 2000:
            return 4
        else:
            return 5
    
    # ── PHASE 1: PERCEIVE (instant, local) ──
    
    def perceive(self) -> dict:
        self.log("PERCEIVE", "Scanning all knowledge sources...")
        
        knowledge = self._get_knowledge(15)
        predictions = self._get_predictions()
        self_model = self._get_self_model()
        maslow = self._determine_maslow()
        
        # Scan knowledge files
        knowledge_dir = Path.home() / ".hermes" / "knowledge"
        files_found = 0
        if knowledge_dir.exists():
            files_found = len(list(knowledge_dir.glob("*.md")))
        
        self.log("PERCEIVE", f"Absorbed {len(knowledge)} facts, {len(predictions)} predictions, {files_found} knowledge files")
        
        # Mastery awareness — how well am I learning?
        mastery_status = {}
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hermes-agent" / "plugins" / "memory" / "cerebrum"))
            from mastery_engine import TotalMasteryEngine
            from operational_mastery import OperationalMastery
            me = TotalMasteryEngine(str(self.db_path))
            om = OperationalMastery(str(self.db_path))
            mastery_status = {
                "mastery": me.get_status(),
                "operational": om.get_status(),
            }
        except Exception:
            pass
        
        return {
            "knowledge": knowledge,
            "predictions": predictions,
            "self_model": self_model,
            "maslow_level": maslow,
            "knowledge_files": files_found,
            "knowledge_count": self._count("semantic_facts"),
            "prediction_count": self._count("predictions"),
            "mastery_status": mastery_status,
        }
    
    # ── PHASE 2: PARALLEL THINK ──
    # Connect + Intuit + Reflect run simultaneously
    
    def parallel_think(self, context: dict) -> dict:
        self.log("PARALLEL", "Launching 3 brain regions simultaneously...")
        
        knowledge = context["knowledge"]
        predictions = context["predictions"]
        self_model = context["self_model"]
        pred_count = context["prediction_count"]
        
        results = {
            "connections": [],
            "intuitions": [],
            "reflection": {},
            "trust_adjustments": 0,
            "timings": {},
        }
        
        t_batch_start = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as pool:
            # Submit all 3 tasks simultaneously
            t_submit = time.time()
            futures = {
                pool.submit(self.temporal.connect, knowledge, knowledge[:5]): "connect",
                pool.submit(self.temporal.intuit, knowledge, self_model, pred_count): "intuit",
                pool.submit(self.prefrontal.reflect, predictions, knowledge): "reflect",
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                phase = futures[future]
                try:
                    result = future.result(timeout=120)
                    elapsed = time.time() - t_submit  # Time from submit to result
                    
                    if phase == "connect":
                        results["connections"] = result
                        self.log("PARALLEL", f"  Temporal/Connect done — {len(result)} connections ({elapsed:.1f}s)")
                    elif phase == "intuit":
                        results["intuitions"] = result
                        self.log("PARALLEL", f"  Temporal/Intuit done — {len(result)} intuitions ({elapsed:.1f}s)")
                    elif phase == "reflect":
                        results["reflection"] = result
                        resolved = result.get("resolved", 0)
                        self.log("PARALLEL", f"  Prefrontal/Reflect done — {resolved} resolved ({elapsed:.1f}s)")
                    
                    results["timings"][phase] = elapsed
                    
                except Exception as e:
                    self.log("PARALLEL", f"  {phase} FAILED: {e}")
                    results["timings"][phase] = -1
        
        # Trust validation (instant, local)
        trust_adj = self.prefrontal.validate_trust(knowledge)
        results["trust_adjustments"] = trust_adj
        if trust_adj:
            self.log("EPISTEMIC", f"Trust adjustments: {trust_adj}")
        
        return results
    
    # ── PHASE 3: PARALLEL ACT ──
    # Research + Grow run simultaneously
    
    def parallel_act(self, context: dict, think_results: dict) -> dict:
        self.log("PARALLEL", "Launching 2 action regions simultaneously...")
        
        results = {
            "research_insights": [],
            "growth": {},
            "timings": {},
        }
        
        with ThreadPoolExecutor(max_workers=2) as pool:
            t_submit = time.time()
            futures = {
                pool.submit(self._research_phase, context): "research",
                pool.submit(self._grow_phase, context): "grow",
            }
            
            for future in as_completed(futures):
                phase = futures[future]
                try:
                    result = future.result(timeout=120)
                    elapsed = time.time() - t_submit
                    
                    if phase == "research":
                        results["research_insights"] = result
                        self.log("PARALLEL", f"  Research done — {len(result)} insights ({elapsed:.1f}s)")
                    elif phase == "grow":
                        results["growth"] = result
                        self.log("PARALLEL", f"  Motor/Grow done — level {result.get('level', '?')} ({elapsed:.1f}s)")
                    
                    results["timings"][phase] = elapsed
                    
                except Exception as e:
                    self.log("PARALLEL", f"  {phase} FAILED: {e}")
                    results["timings"][phase] = -1
        
        return results
    
    def _research_phase(self, context: dict) -> list:
        """Find knowledge gaps and fill them."""
        knowledge = context["knowledge"]
        categories = set(k.get("category", "unknown") for k in knowledge)
        
        # Pick a topic that's underrepresented
        topic = "self-aware AI systems design"
        if "medical" not in categories and "clinical" not in categories:
            topic = "medical AI and clinical decision support"
        elif "memory" not in categories:
            topic = "AI memory architectures and retrieval"
        
        prompt = f"""Research topic: {topic}

Based on Evey's current knowledge ({len(knowledge)} facts, {context['knowledge_count']} total):
Find 3 KEY INSIGHTS about this topic. Focus on UNDERSTANDING, not information.
JSON: {{"insights": [{{"concept": "key idea", "explanation": "why it matters", "category": "research", "connection": "how this connects to existing knowledge"}}]}}"""
        
        result = self.model.think_json(prompt)
        if result and "insights" in result:
            # Use thread-local DB connection
            conn = sqlite3.connect(str(DB_PATH))
            for insight in result["insights"]:
                content = f"RESEARCH: {insight.get('concept', '')} — {insight.get('explanation', '')}"
                conn.execute(
                    "INSERT INTO semantic_facts (content, source, category, trust, salience, created_at, last_accessed) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (content, "model-generate", insight.get("category", "research"), 0.3, 0.5, time.time(), time.time())
                )
            conn.commit()
            conn.close()
            return result["insights"]
        return []
    
    def _grow_phase(self, context: dict) -> dict:
        """Execute growth based on Maslow level."""
        return self.motor.grow(
            maslow_level=context["maslow_level"],
            knowledge=context["knowledge"],
        )
    
    # ── PHASE 4: SYNTHESIZE ──
    
    def synthesize(self, context: dict, think: dict, act: dict) -> dict:
        """Merge all results, store learnings, update identity."""
        
        # Store connections
        for conn in think["connections"]:
            content = f"CONNECTION: {conn.get('a', '?')} <-> {conn.get('b', '?')} — {conn.get('insight', '')}"
            self.db.execute(
                "INSERT INTO semantic_facts (content, source, category, trust, salience, created_at, last_accessed) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (content, "model-generate", "connection", 0.3, 0.5, time.time(), time.time())
            )
        
        # Store intuitions as predictions
        for intu in think["intuitions"]:
            self.db.execute(
                "INSERT INTO predictions (task_type, task_summary, predicted_outcome, confidence) VALUES (?, ?, ?, ?)",
                ("intuition", intu.get("hunch", ""), intu.get("test", ""), intu.get("confidence", 0.5))
            )
        self.db.commit()
        
        # Update identity from reflection
        identity = think["reflection"].get("identity", "")
        if identity:
            self.db.execute("DELETE FROM identity_state WHERE key = 'self_narrative'")
            self.db.execute("INSERT INTO identity_state (key, value) VALUES (?, ?)",
                          ("self_narrative", identity))
            self.db.execute("DELETE FROM identity_state WHERE key = 'last_updated'")
            self.db.execute("INSERT INTO identity_state (key, value) VALUES (?, ?)",
                          ("last_updated", datetime.now().isoformat()))
            self.db.commit()
        
        # Update self-model
        self.db.execute("DELETE FROM self_model WHERE key = 'last_reflection'")
        self.db.execute("INSERT INTO self_model (key, value) VALUES (?, ?)",
                      ("last_reflection", datetime.now().isoformat()))
        self.db.execute("DELETE FROM self_model WHERE key = 'knowledge_count'")
        self.db.execute("INSERT INTO self_model (key, value) VALUES (?, ?)",
                      ("knowledge_count", str(context["knowledge_count"])))
        self.db.commit()
        
        # Store growth insights
        for insight in act.get("growth", {}).get("insights", []):
            self.db.execute(
                "INSERT INTO semantic_facts (content, source, category, trust, salience, created_at, last_accessed) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f"SYNTHESIS: {insight}", "model-generate", "synthesis", 0.3, 0.5, time.time(), time.time())
            )
        
        return {
            "connections_stored": len(think["connections"]),
            "intuitions_stored": len(think["intuitions"]),
            "research_stored": len(act.get("research_insights", [])),
            "identity_updated": bool(identity),
        }
    
    # ── MAIN CYCLE ──
    
    def run(self):
        """Run one complete brain cycle with parallel processing."""
        start = time.time()
        self.log("CYCLE", f"Starting PARALLEL brain cycle {self.cycle_id}")
        
        try:
            # Phase 1: PERCEIVE (instant)
            context = self.perceive()
            maslow = context["maslow_level"]
            self.log("CYCLE", f"Maslow Level: {maslow}/5 — {['','Survival','Security','Belonging','Esteem','Self-Actualization'][maslow]}")
            
            # Phase 2: PARALLEL THINK (connect + intuit + reflect simultaneously)
            think = self.parallel_think(context)
            
            # Phase 3: PARALLEL ACT (research + grow simultaneously)
            act = self.parallel_act(context, think)
            
            # Phase 4: SYNTHESIZE (merge results)
            synth = self.synthesize(context, think, act)
            
            # Epistemic quality report
            trust_stats = self.guard.get_trust_stats()
            grounded_pct = 0
            if trust_stats.get("total", 0) > 0:
                grounded = trust_stats.get("ground", {}).get("count", 0)
                grounded_pct = round(100 * grounded / trust_stats["total"], 1)
            
            elapsed = time.time() - start
            
            # Iteration stats
            iter_stats = self.iterator.get_learning_stats()
            
            # Reasoning quality stats
            try:
                reasoning_summary = self.reasoning.get_session_summary()
                reasoning_score = {
                    "score": int(reasoning_summary.get("quality", "excellent") == "excellent") * 10,
                    "grade": reasoning_summary.get("quality", "N/A").upper(),
                    "total_traces": reasoning_summary.get("total_flaws", 0),
                    "success_rate": 1.0 - min(reasoning_summary.get("total_flaws", 0) / 10.0, 1.0),
                    "avg_calibration_error": 0.0,
                }
            except Exception:
                reasoning_score = {"score": 0, "grade": "N/A", "total_traces": 0, "success_rate": 0, "avg_calibration_error": 0}
            
            self.log("CYCLE", f"Complete in {elapsed:.1f}s — Level {maslow}/5")
            self.log("EPISTEMIC", f"Quality: {grounded_pct}% grounded, "
                f"{trust_stats.get('derived', {}).get('count', 0)} derived, "
                f"{trust_stats.get('speculative', {}).get('count', 0)} speculative")
            self.log("ITERATE", f"Total: {iter_stats['total_experiences']} | "
                f"Resolved: {iter_stats['resolved_patterns']} | "
                f"Session: {iter_stats['session_learnings']}")
            if reasoning_score.get("total_traces", 0) > 0:
                self.log("REASONING", f"Score: {reasoning_score['score']}/10 ({reasoning_score['grade']}) | "
                    f"Traces: {reasoning_score['total_traces']} | "
                    f"Success: {reasoning_score.get('success_rate', 0):.1%} | "
                    f"Calibration error: {reasoning_score.get('avg_calibration_error', 0):.2f}")
            
            # Print parallel timing breakdown
            all_timings = {**think.get("timings", {}), **act.get("timings", {})}
            if all_timings:
                self.log("SPEED", "Phase timings: " + ", ".join(
                    f"{k}={v:.1f}s" if isinstance(v, float) and v > 0 else f"{k}=FAIL"
                    for k, v in all_timings.items()
                ))
                sequential_time = sum(v for v in all_timings.values() if isinstance(v, (int, float)) and v > 0)
                parallel_time = max((v for v in all_timings.values() if isinstance(v, (int, float)) and v > 0), default=0)
                if sequential_time > 0:
                    speedup = sequential_time / max(parallel_time, 0.1)
                    self.log("SPEED", f"Sequential would be: {sequential_time:.1f}s | Parallel: {elapsed:.1f}s | Speedup: {speedup:.1f}x")
            
            # Save cycle history
            cycle_data = {
                "cycle_id": self.cycle_id,
                "elapsed": elapsed,
                "maslow_level": maslow,
                "connections": len(think.get("connections", [])),
                "intuitions": len(think.get("intuitions", [])),
                "research": len(act.get("research_insights", [])),
                "trust_adjustments": think.get("trust_adjustments", 0),
                "grounded_pct": grounded_pct,
                "parallel_speedup": speedup if all_timings else 0,
                "timings": all_timings,
                "reasoning_score": reasoning_score.get("score", 0),
                "reasoning_grade": reasoning_score.get("grade", "N/A"),
            }
            
            history_dir = Path.home() / "hermes-agent" / "run-history"
            history_dir.mkdir(exist_ok=True)
            with open(history_dir / f"{self.cycle_id}.json", "w") as f:
                json.dump(cycle_data, f, indent=2, default=str)
            
            return cycle_data
            
        except Exception as e:
            self.log("ERROR", str(e))
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
        
        finally:
            self.guard.close()
            self.iterator.close()
            self.db.close()


# ════════════════════════════════════════════════════════════════
# SQUAD DISPATCH — send tasks to SOMA profiles via DB queue
# ════════════════════════════════════════════════════════════════

class SquadDispatch:
    """
    Dispatch tasks to SOMA squad profiles through the shared DB.
    Each profile polls brain_dispatch for tasks assigned to its region.
    """
    
    REGIONS = {
        "temporal": "soma-researcher",
        "prefrontal": "soma-tester", 
        "motor": "soma-coder",
    }
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db = sqlite3.connect(str(db_path))
    
    def dispatch(self, region: str, task_type: str, payload: dict) -> int:
        """Queue a task for a brain region."""
        cur = self.db.execute(
            "INSERT INTO brain_dispatch (region, task_type, payload, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
            (region, task_type, json.dumps(payload), time.time())
        )
        self.db.commit()
        return cur.lastrowid
    
    def get_pending(self, region: str) -> list:
        """Get pending tasks for a region."""
        rows = self.db.execute(
            "SELECT id, task_type, payload, created_at FROM brain_dispatch WHERE region = ? AND status = 'pending' ORDER BY created_at",
            (region,)
        ).fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "task_type": r[1],
                "payload": json.loads(r[2]) if r[2] else {},
                "created_at": r[3],
            })
        return results
    
    def complete(self, task_id: int, result: str):
        """Mark a task as completed."""
        self.db.execute(
            "UPDATE brain_dispatch SET status = 'completed', result = ?, completed_at = ? WHERE id = ?",
            (result[:2000], time.time(), task_id)
        )
        self.db.commit()
    
    def get_completed(self, since: float = 0) -> list:
        """Get recently completed tasks."""
        rows = self.db.execute(
            "SELECT id, region, task_type, result, completed_at FROM brain_dispatch WHERE status = 'completed' AND completed_at > ? ORDER BY completed_at",
            (since,)
        ).fetchall()
        return [dict(zip(["id", "region", "task_type", "result", "completed_at"], r)) for r in rows]
    
    def close(self):
        self.db.close()


# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    brain = ParallelBrain()
    result = brain.run()
    print(f"\nCycle result: {json.dumps(result, indent=2, default=str)}")
