"""
episodic_memory.py — R25: Generative Semantic Workspace (GSW) inspired episodic memory.

Paper: arXiv:2511.07587 (AAAI 2026 Oral) "Beyond Fact Retrieval: Episodic Memory for RAG 
with Generative Semantic Workspaces"

Architecture:
  Operator: Maps incoming observations (tool calls, outcomes) to semantic structures
  Reconciler: Integrates structures into persistent workspace, enforces temporal coherence
  Retriever: Query-time retrieval of similar past experiences + tips for context injection

Cortex DB Integration:
  - Reads from cortex_nodes (experience, tip, fact, observation, world)
  - Uses pgvector HNSW index for similarity search
  - Writes consolidated schemas back as new nodes

Wired in:
  post_tool_call: Operator captures tool outcomes → stores episodic traces
  pre_llm_call: Retriever injects relevant past experiences into context
"""

import json
import time
import threading
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List

# Domain normalization: raw tool/action domains → canonical domains
_CANONICAL_DOMAIN_MAP = {
    'web_research': 'research', 'web_search': 'research', 'web_extract': 'research',
    'search_files': 'research', 'knowledge_search': 'research', 'news_scan': 'research',
    'terminal': 'coding', 'execute_code': 'coding', 'patch': 'coding',
    'write_file': 'coding', 'read_file': 'coding', 'process': 'coding',
    'delegate_with_model': 'agent_architecture', 'delegate_parallel': 'agent_architecture',
    'delegate_task': 'agent_architecture', 'cached_delegate': 'agent_architecture',
    'memory': 'memory', 'metacognition': 'memory', 'recollection': 'memory',
    'session_search': 'memory',
    'skill_manage': 'meta', 'skill_view': 'meta',
    'autonomous_decide': 'self-improvement', 'execution': 'coding',
    'delegation': 'agent_architecture', 'exploration': 'research',
    'perception': 'research', 'debugging': 'coding', 'general': 'tool_usage',
    'distillation_cycle': 'self-improvement', 'deep_work': 'self-improvement',
    'deep_cycle': 'self-improvement', 'hindsight': 'self-improvement',
    'distilled_knowledge': 'self-improvement', 'generic': 'tool_usage',
    'evey_goals': 'planning', 'cronjob': 'planning',
    'consolidate_daily_memory': 'self-improvement', 'update_identity': 'self-improvement',
    'learn_from_interaction': 'self-improvement', 'apply_learnings': 'self-improvement',
    'habits_log': 'self-improvement', 'habits_insights': 'self-improvement',
    'cost_check': 'agent_evaluation', 'telemetry_query': 'agent_evaluation',
    'telegram_card': 'agent_architecture', 'send_message': 'agent_architecture',
}

def _normalize_domain(raw_domain: str) -> str:
    """Map any raw domain name to a canonical domain."""
    if not raw_domain:
        return 'tool_usage'
    return _CANONICAL_DOMAIN_MAP.get(raw_domain, raw_domain if raw_domain in {
        'tool_usage', 'agent_architecture', 'coding', 'reasoning', 'meta',
        'self-improvement', 'research', 'memory', 'training', 'agent_evaluation',
        'planning', 'security', 'cost'
    } else 'tool_usage')

# Thread-safe singleton
_instances = {}
_instance_lock = threading.Lock()


def get_instance(session_id: str = "default"):
    """Get or create the singleton EpisodicMemory instance."""
    with _instance_lock:
        if 'episodic_memory' not in _instances:
            _instances['episodic_memory'] = EpisodicMemory()
        return _instances['episodic_memory']


def _get_db():
    """Get Cortex DB connection."""
    try:
        import psycopg2
        return psycopg2.connect(
            'postgresql://hindsight:hindsight@localhost:5432/cortex',
            keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3
        )
    except Exception:
        return None


class EpisodicBuffer:
    """Short-term sliding window of recent episodes (in-memory)."""
    
    def __init__(self, max_size=500):
        self.max_size = max_size
        self.buffer = []
        self._lock = threading.Lock()
    
    def add(self, episode: Dict):
        with self._lock:
            episode['buffer_ts'] = time.time()
            self.buffer.append(episode)
            if len(self.buffer) > self.max_size:
                self.buffer = self.buffer[-self.max_size:]
    
    def get_recent(self, n=20) -> List[Dict]:
        with self._lock:
            return list(self.buffer[-n:])
    
    def get_by_domain(self, domain: str, n=10) -> List[Dict]:
        with self._lock:
            matches = [e for e in self.buffer if e.get('domain') == domain]
            return matches[-n:]
    
    def size(self) -> int:
        with self._lock:
            return len(self.buffer)


class Operator:
    """Maps incoming observations to semantic structures (GSW Operator)."""
    
    def __init__(self):
        self.action_patterns = {}
        self._pattern_lock = threading.Lock()
    
    def observe(self, tool_name: str, tool_args: Dict, result_summary: str,
                success: bool, duration_ms: float, context_tags: List[str] = None) -> Dict:
        episode = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': {
                'tool': tool_name,
                'args_hash': hashlib.md5(
                    json.dumps(tool_args, sort_keys=True, default=str).encode()
                ).hexdigest()[:12],
                'args_keys': list(tool_args.keys()) if isinstance(tool_args, dict) else [],
            },
            'outcome': {
                'success': success,
                'duration_ms': round(duration_ms, 1),
                'result_snippet': result_summary[:300] if result_summary else '',
            },
            'semantic': self._extract_semantics(tool_name, success, duration_ms, context_tags),
            'tags': context_tags or [],
            'domain': self._infer_domain(tool_name, context_tags),
        }
        
        pattern_key = f"{tool_name}:{'ok' if success else 'fail'}"
        with self._pattern_lock:
            if pattern_key not in self.action_patterns:
                self.action_patterns[pattern_key] = {'count': 0, 'avg_duration': 0}
            p = self.action_patterns[pattern_key]
            p['count'] += 1
            p['avg_duration'] = (p['avg_duration'] * (p['count'] - 1) + duration_ms) / p['count']
            episode['pattern_frequency'] = p['count']
            episode['pattern_is_novel'] = p['count'] <= 3
        
        return episode
    
    def _extract_semantics(self, tool_name, success, duration_ms, tags):
        if success and duration_ms < 2000:
            quality = 'fast_success'
        elif success and duration_ms < 10000:
            quality = 'normal_success'
        elif success:
            quality = 'slow_success'
        elif duration_ms < 5000:
            quality = 'fast_failure'
        else:
            quality = 'slow_failure'
        
        return {
            'quality': quality,
            'is_success': success,
            'efficiency': 'high' if success and duration_ms < 3000 else 
                         'medium' if success else 'low',
        }
    
    def _infer_domain(self, tool_name, tags):
        # MUST use canonical domains from cortex_compat.py CANONICAL_DOMAINS
        domain_map = {
            'web_research': 'research', 'web_search': 'research', 'web_extract': 'research',
            'search_files': 'research', 'knowledge_search': 'research', 'news_scan': 'research',
            'browser_navigate': 'research', 'browser_snapshot': 'research',
            'browser_click': 'research', 'browser_type': 'research',
            'browser_console': 'research', 'browser_vision': 'research',
            'vision_analyze': 'research', 'verify_url': 'research', 'verify_repo': 'research',
            'terminal': 'coding', 'execute_code': 'coding', 'patch': 'coding',
            'write_file': 'coding', 'read_file': 'coding', 'process': 'coding',
            'delegate_with_model': 'agent_architecture', 'delegate_parallel': 'agent_architecture',
            'delegate_task': 'agent_architecture', 'cached_delegate': 'agent_architecture',
            'validate_output': 'agent_architecture',
            'memory': 'memory', 'memory_score': 'memory', 'memory_decay': 'memory',
            'session_search': 'memory', 'skill_manage': 'meta', 'skill_view': 'meta',
            'autonomous_decide': 'self-improvement', 'update_identity': 'self-improvement',
            'learn_from_interaction': 'self-improvement', 'apply_learnings': 'self-improvement',
            'consolidate_daily_memory': 'self-improvement', 'habits_log': 'self-improvement',
            'cost_check': 'agent_evaluation', 'telemetry_query': 'agent_evaluation',
            'cronjob': 'planning', 'schedule_add': 'planning',
            'telegram_card': 'agent_architecture', 'send_message': 'agent_architecture',
        }
        if tool_name in domain_map:
            return domain_map[tool_name]
        tag_str = ' '.join(tags or []).lower()
        if 'debug' in tag_str or 'error' in tag_str:
            return 'coding'
        if 'research' in tag_str:
            return 'research'
        if 'memory' in tag_str or 'session' in tag_str:
            return 'memory'
        return 'tool_usage'


class Reconciler:
    """Integrates observations into persistent Cortex workspace (GSW Reconciler)."""
    
    CONSOLIDATION_INTERVAL = 20  # Lowered from 50: consolidate more often
    
    def __init__(self):
        self.observation_count = 0
    
    def maybe_consolidate(self, buffer: EpisodicBuffer) -> Optional[Dict]:
        self.observation_count += 1
        if self.observation_count % self.CONSOLIDATION_INTERVAL != 0:
            return None
        return self._run_consolidation(buffer)
    
    def _run_consolidation(self, buffer: EpisodicBuffer) -> Dict:
        recent = buffer.get_recent(50)
        if not recent:
            return {'consolidated': 0, 'schemas': 0}
        
        clusters = {}
        for ep in recent:
            key = f"{ep.get('domain', 'unknown')}:{ep['semantic']['quality']}"
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(ep)
        
        schemas = []
        for cluster_key, episodes in clusters.items():
            if len(episodes) >= 2:  # Lowered from 3: easier clustering
                tool_counts = {}
                for ep in episodes:
                    t = ep['action']['tool']
                    tool_counts[t] = tool_counts.get(t, 0) + 1
                schemas.append({
                    'pattern': cluster_key,
                    'frequency': len(episodes),
                    'dominant_tool': max(tool_counts, key=tool_counts.get),
                    'avg_duration': sum(e['outcome']['duration_ms'] for e in episodes) / len(episodes),
                    'success_rate': sum(1 for e in episodes if e['outcome']['success']) / len(episodes),
                })
        
        written = 0
        conn = _get_db()
        if conn:
            try:
                cur = conn.cursor()
                for schema in schemas:
                    try:
                        text = json.dumps({
                            'schema_type': 'episodic_pattern',
                            'pattern': schema['pattern'],
                            'frequency': schema['frequency'],
                            'dominant_tool': schema['dominant_tool'],
                            'avg_duration_ms': round(schema['avg_duration'], 1),
                            'success_rate': round(schema['success_rate'], 2),
                        })
                        cur.execute(
                            """INSERT INTO cortex_nodes 
                            (id, text, node_type, domain, elo, confidence, salience,
                             frequency, is_active, created_at, updated_at, access_count)
                            VALUES (uuid_generate_v4(), %s, 'experience', %s, 1200, 0.7, 0.8,
                             %s, true, NOW(), NOW(), 0)""",
                            (text, _normalize_domain(schema['pattern'].split(':')[0]), schema['frequency'])
                        )
                        written += 1
                    except Exception:
                        conn.rollback()
                        continue
                conn.commit()
            except Exception:
                pass
            finally:
                conn.close()
        
        return {'consolidated': len(recent), 'schemas_found': len(schemas), 'schemas_written': written}


class Retriever:
    """
    Query-time retrieval of relevant past experiences and tips.
    Two-path retrieval: (1) domain-matched high-Elo tips, 
    (2) keyword + domain matched high-Elo experiences.
    """

    # Map tool names to canonical domains for query routing
    _TOOL_DOMAIN = {
        'web_research': 'research', 'web_search': 'research', 'web_extract': 'research',
        'terminal': 'coding', 'execute_code': 'coding', 'patch': 'coding',
        'write_file': 'coding', 'read_file': 'coding', 'process': 'coding',
        'delegate_with_model': 'agent_architecture', 'delegate_parallel': 'agent_architecture',
        'delegate_task': 'agent_architecture', 'cached_delegate': 'agent_architecture',
        'memory': 'memory', 'memory_score': 'memory', 'memory_decay': 'memory',
        'session_search': 'memory', 'skill_manage': 'meta', 'skill_view': 'meta',
        'autonomous_decide': 'self-improvement', 'update_identity': 'self-improvement',
        'learn_from_interaction': 'self-improvement', 'apply_learnings': 'self-improvement',
        'consolidate_daily_memory': 'self-improvement', 'habits_log': 'self-improvement',
        'cost_check': 'agent_evaluation', 'telemetry_query': 'agent_evaluation',
        'cronjob': 'planning', 'schedule_add': 'planning',
        'telegram_card': 'agent_architecture', 'send_message': 'agent_architecture',
        'browser_navigate': 'research', 'browser_snapshot': 'research',
        'browser_click': 'research', 'vision_analyze': 'research',
        'validate_output': 'agent_architecture', 'search_files': 'research',
        'knowledge_search': 'research', 'save_finding': 'research',
    }

    def __init__(self, top_k=5, min_tip_elo=1400, min_exp_elo=1150):
        self.top_k = top_k
        self.min_tip_elo = min_tip_elo
        self.min_exp_elo = min_exp_elo

    def retrieve_for_context(self, current_task: str, tool_name: str = None,
                             domain: str = None) -> Dict:
        results = {'tips': [], 'experiences': [], 'injection_text': '', 'stats': {'retrieved': 0}}

        conn = _get_db()
        if not conn:
            return results

        try:
            cur = conn.cursor()

            # Infer domain from tool_name if not provided
            inferred_domain = domain or (self._TOOL_DOMAIN.get(tool_name) if tool_name else None)

            # ── Path 1: High-Elo tips (domain-matched) ──
            tip_params = []
            tip_where_clauses = ["node_type = 'tip'", "is_active = true", "elo >= %s"]
            tip_params.append(self.min_tip_elo)
            if inferred_domain:
                tip_where_clauses.append("domain = %s")
                tip_params.append(inferred_domain)

            tip_where = " AND ".join(tip_where_clauses)
            cur.execute(
                f"""SELECT id, text, domain, elo, confidence
                    FROM cortex_nodes 
                    WHERE {tip_where}
                    ORDER BY elo DESC LIMIT %s""",
                tip_params + [self.top_k]
            )

            for row in cur.fetchall():
                try:
                    tip_data = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                except (json.JSONDecodeError, TypeError):
                    tip_data = {'raw': str(row[1])[:200]}
                results['tips'].append({
                    'id': str(row[0]), 'data': tip_data, 'domain': row[2],
                    'elo': float(row[3]) if row[3] else 1200,
                })

            # ── Path 2: High-value natural language experiences ──
            # Skip JSON action_hash blobs (no injection value)
            # Rank by: Elo DESC, domain match, salience
            # action_hash prefix to exclude via parameterized LIKE
            _ah_prefix = '{"action_hash":%'
            exp_where_clauses = [
                "node_type = 'experience'", "is_active = true",
                "elo >= %s",
                "text NOT LIKE %s",  # skip raw action logs (parameterized)
                "length(text) > 50",
            ]
            exp_params = [self.min_exp_elo, _ah_prefix]
            if inferred_domain:
                exp_where_clauses.append("domain = %s")
                exp_params.append(inferred_domain)

            exp_where = " AND ".join(exp_where_clauses)
            cur.execute(
                f"""SELECT id, text, domain, elo, salience
                    FROM cortex_nodes 
                    WHERE {exp_where}
                    ORDER BY elo DESC, salience DESC LIMIT %s""",
                exp_params + [3]
            )

            for row in cur.fetchall():
                try:
                    exp_data = json.loads(row[1]) if isinstance(row[1], str) and row[1].startswith('{') else row[1]
                except (json.JSONDecodeError, TypeError):
                    exp_data = {'raw': str(row[1])[:200]}
                results['experiences'].append({
                    'id': str(row[0]), 'data': exp_data, 'domain': row[2],
                    'elo': float(row[3]) if row[3] else 1200,
                    'salience': float(row[4]) if row[4] else 0.5,
                })

            # ── Path 2.5: Keyword fallback if domain match returns < 2 ──
            if len(results['experiences']) < 2:
                task_kw = [w for w in current_task.lower().split()[:5] if len(w) > 3]
                if task_kw:
                    kw_conds = " OR ".join(["text ILIKE %s" for _ in task_kw])
                    kw_params = [f'%{kw}%' for kw in task_kw]
                    cur.execute(
                        f"""SELECT id, text, domain, elo, salience
                            FROM cortex_nodes 
                            WHERE node_type = 'experience' AND is_active = true
                            AND elo >= %s AND text NOT LIKE %s
                            AND ({kw_conds})
                            ORDER BY elo DESC LIMIT 3""",
                        [self.min_exp_elo, _ah_prefix] + kw_params
                    )
                    seen_ids = {e['id'] for e in results['experiences']}
                    for row in cur.fetchall():
                        eid = str(row[0])
                        if eid in seen_ids:
                            continue
                        seen_ids.add(eid)
                        try:
                            exp_data = json.loads(row[1]) if isinstance(row[1], str) and row[1].startswith('{') else row[1]
                        except (json.JSONDecodeError, TypeError):
                            exp_data = {'raw': str(row[1])[:200]}
                        results['experiences'].append({
                            'id': eid, 'data': exp_data, 'domain': row[2],
                            'elo': float(row[3]) if row[3] else 1200,
                            'salience': float(row[4]) if row[4] else 0.5,
                        })

            # ── Path 3: Build injection text ──
            parts = []
            if results['tips']:
                parts.append("[EPISODIC MEMORY — Retrieved Tips]")
                for tip in results['tips'][:3]:
                    d = tip['data']
                    if isinstance(d, dict):
                        cond = d.get('condition', '')[:80]
                        rec = d.get('recommendation', '')[:80]
                        if cond and rec:
                            parts.append(f"  Elo={tip['elo']:.0f}: IF {cond} THEN {rec}")
                        else:
                            raw = d.get('raw', '')[:120]
                            if raw:
                                parts.append(f"  Elo={tip['elo']:.0f}: {raw}")
                    else:
                        parts.append(f"  Elo={tip['elo']:.0f}: {str(d)[:120]}")

            if results['experiences']:
                parts.append("[EPISODIC MEMORY — Relevant Experiences]")
                for exp in results['experiences'][:3]:
                    d = exp['data']
                    lesson = ''
                    if isinstance(d, dict):
                        lesson = d.get('lesson', '') or d.get('recommendation', '')
                        if not lesson:
                            atype = d.get('action_type', '')
                            adetail = d.get('action_detail', '')
                            if atype or adetail:
                                lesson = f"{atype}: {adetail}"
                    if not lesson:
                        lesson = str(d)[:120] if d else ''
                    elo_str = f"Elo={exp.get('elo', 0):.0f}"
                    parts.append(f"  {elo_str}: {str(lesson)[:120]}")

            results['injection_text'] = '\n'.join(parts)
            results['stats']['retrieved'] = len(results['tips']) + len(results['experiences'])

        except Exception as e:
            results['error'] = str(e)
        finally:
            conn.close()

        return results


class EpisodicMemory:
    """
    R25: GSW-inspired Episodic Memory.
    post_tool_call: capture() → stores episodic traces
    pre_llm_call: retrieve() → injects relevant past context
    """
    
    def __init__(self):
        self.buffer = EpisodicBuffer(max_size=500)
        self.operator = Operator()
        self.reconciler = Reconciler()
        self.retriever = Retriever(top_k=5, min_tip_elo=1400, min_exp_elo=1150)
        self._call_count = 0
        self._last_retrieval = None
    
    def capture(self, tool_name, tool_args, result_summary, success, duration_ms, context_tags=None):
        episode = self.operator.observe(tool_name, tool_args, result_summary, success, duration_ms, context_tags)
        self.buffer.add(episode)
        consolidation = self.reconciler.maybe_consolidate(self.buffer)
        self._call_count += 1
        
        result = {
            'captured': True,
            'domain': episode['domain'],
            'quality': episode['semantic']['quality'],
            'is_novel': episode.get('pattern_is_novel', False),
            'buffer_size': self.buffer.size(),
            'calls': self._call_count,
        }
        if consolidation:
            result['consolidation'] = consolidation
        return result
    
    def retrieve(self, current_task, tool_name=None, domain=None):
        retrieval = self.retriever.retrieve_for_context(current_task, tool_name, domain)
        self._last_retrieval = retrieval
        return retrieval
    
    def get_stats(self):
        return {
            'buffer_size': self.buffer.size(),
            'call_count': self._call_count,
            'last_retrieval_count': self._last_retrieval['stats']['retrieved'] if self._last_retrieval else 0,
        }

    def build_injection(self, context="") -> str:
        """Utility module — no context injection"""
        return ""
