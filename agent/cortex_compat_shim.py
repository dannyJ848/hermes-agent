#!/usr/bin/env python3
"""
cortex_compat_shim.py — Universal SQLite→Cortex proxy.

Drop-in replacement for sqlite3.connect('cerebrum_memory.db').
Routes ALL reads/writes to Cortex PostgreSQL. Falls back to SQLite
only if Postgres is unreachable.

USAGE (in any agent/ module):
    # OLD:
    #   conn = sqlite3.connect(DB_PATH, timeout=5)
    # NEW:
    from cortex_compat_shim import connect
    conn = connect(DB_PATH)  # Returns a CortexConnection that quacks like sqlite3.Connection

ARCHITECTURE:
    - CortexConnection wraps psycopg2, speaks sqlite3 API
    - Translates SQLite table names → Cortex table names
    - Translates SQLite SQL dialect → PostgreSQL dialect
    - Auto-handles: ? vs %s params, AUTOINCREMENT, INTEGER PRIMARY KEY, etc.
    - Unknown tables → stored in Cortex generic key-value store
    - If Postgres down → transparent fallback to real SQLite
"""

import sys
import os
import re
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger("cortex_shim")

# ── Cortex connection (from env var, fallback for dev) ──
CORTEX_DSN = os.environ.get('CORTEX_DSN', 'postgresql://hindsight:hindsight@localhost:5432/cortex')

# ── Table name mapping: SQLite → Cortex ──
TABLE_MAP = {
    'distilled_tips': 'cortex_nodes',       # tips → cortex_nodes WHERE node_type='tip'
    'tip_elo': 'cortex_eval_history',        # Elo ratings
    'semantic_facts': 'cortex_nodes',        # facts → cortex_nodes WHERE node_type='fact'
    'episodic_memory': 'cortex_nodes',       # episodes → cortex_nodes WHERE node_type='episode'
    'experiences': 'cortex_nodes',            # experiences → cortex_nodes WHERE node_type='experience'
    'tool_stats': 'cortex_tool_calls',       # tool usage
    'tool_cache': 'cortex_mastery',          # tool mastery
    'tool_performance': 'cortex_mastery',    # tool performance
    'tool_mastery': 'cortex_mastery',        # mastery scores
    'mastery_scores': 'cortex_mastery',      # mastery scores
    'predictions': 'cortex_predictions',     # predictions
    'call_log': 'cortex_tool_calls',         # call logging
    'reasoning_chains': 'cortex_reasoning',  # reasoning traces
    'reasoning_traces': 'cortex_reasoning',
    'exploration_log': 'cortex_exploration',
    'exploration_tasks': 'cortex_exploration',
    'calibration_data': 'cortex_predictions',
    'domain_calibration': 'cortex_predictions',
    'self_model': 'cortex_nodes',
    'identity_state': 'cortex_nodes',
    'research': 'cortex_documents',
    'plans': 'cortex_nodes',
    'workspace': 'cortex_nodes',
    'propositions': 'cortex_nodes',
    'heuristics': 'cortex_nodes',
    'meta_insights': 'cortex_nodes',
    'ideation_memory': 'cortex_nodes',
    'node_tree': 'cortex_nodes',
    'step_rewards': 'cortex_step_rewards',
    'token_usage': 'cortex_token_usage',
    'debug_sessions': 'cortex_debug_sessions',
    'session_outcomes': 'cortex_nodes',
    'action_history': 'cortex_nodes',
    'strategy_stats': 'cortex_nodes',
    'skills': 'cortex_nodes',
    'skill_versions': 'cortex_nodes',
    'experience_traces': 'cortex_nodes',
    'recovery_strategies': 'cortex_nodes',
    'failure_cases': 'cortex_nodes',
    'retrieval_handles': 'cortex_nodes',
    'flow_nodes': 'cortex_nodes',
    'flow_edges': 'cortex_edges',
    'circuit_breakers': 'cortex_nodes',
    'versions': 'cortex_nodes',
}

# For any table NOT in the map, use a generic JSON store in cortex
GENERIC_TABLE = 'cortex_kv_store'

# Save original sqlite3.connect BEFORE any patching — prevents infinite recursion
import sqlite3 as _sqlite3_module
_ORIGINAL_CONNECT = _sqlite3_module.connect


def _get_pg_conn():
    """Get a psycopg2 connection to Cortex."""
    try:
        import psycopg2
        conn = psycopg2.connect(CORTEX_DSN)
        conn.autocommit = False
        return conn
    except Exception:
        return None


def _ensure_kv_store(conn):
    """Create the generic key-value table if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cortex_kv_store (
                id SERIAL PRIMARY KEY,
                table_name TEXT NOT NULL,
                key TEXT,
                data JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_kv_table ON cortex_kv_store (table_name)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_kv_table_key ON cortex_kv_store (table_name, key)
        """)
    conn.commit()


class CortexCursor:
    """Mimics sqlite3.Cursor but routes to Cortex PostgreSQL."""
    
    def __init__(self, pg_conn, sqlite_fallback_conn=None):
        self._pg = pg_conn
        self._pg_cur = pg_conn.cursor()
        self._sqlite_fallback = sqlite_fallback_conn
        self._sqlite_cur = None
        self._last_rows = []
        self._rowcount = -1
        self._description = None
        self._last_table = None
        self._use_pg = True
    
    def _fallback_sqlite(self):
        """Get or create SQLite fallback cursor."""
        if self._sqlite_cur is None and self._sqlite_fallback:
            self._sqlite_cur = self._sqlite_fallback.cursor()
        return self._sqlite_cur
    
    def _extract_table(self, sql):
        """Extract table name from SQL."""
        sql_upper = sql.strip().upper()
        for pattern, prefixes in [
            (r'FROM\s+"?(\w+)"?', ['SELECT']),
            (r'INTO\s+"?(\w+)"?', ['INSERT', 'REPLACE']),
            (r'UPDATE\s+"?(\w+)"?', ['UPDATE']),
            (r'DELETE\s+FROM\s+"?(\w+)"?', ['DELETE']),
            (r'TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"?(\w+)"?', ['CREATE']),
        ]:
            prefix = sql_upper.split()[0] if sql_upper else ''
            m = re.search(pattern, sql, re.IGNORECASE)
            if m and any(prefix.startswith(p) for p in prefixes):
                return m.group(1).lower()
        return None
    
    def _is_mapped(self, table):
        """Check if this SQLite table maps to Cortex."""
        return table and table.lower() in TABLE_MAP
    
    def _translate_sql(self, sql, params=None):
        """Translate SQLite SQL → PostgreSQL SQL."""
        table = self._extract_table(sql)
        self._last_table = table
        
        if not table or not self._is_mapped(table):
            return None, None  # Route to KV store or SQLite fallback
        
        cortex_table = TABLE_MAP[table.lower()]
        
        # Replace table name
        sql_pg = re.sub(
            r'\b' + re.escape(table) + r'\b',
            cortex_table,
            sql,
            count=0,
            flags=re.IGNORECASE
        )
        
        # Replace ? placeholders with %s
        sql_pg = sql_pg.replace('?', '%s')
        
        # Replace SQLite-specific syntax
        sql_pg = sql_pg.replace('AUTOINCREMENT', '')
        sql_pg = re.sub(r'INTEGER\s+PRIMARY\s+KEY', 'UUID DEFAULT gen_random_uuid()', sql_pg, flags=re.IGNORECASE)
        sql_pg = re.sub(r'\bDATETIME\b', 'TIMESTAMPTZ', sql_pg, flags=re.IGNORECASE)
        sql_pg = re.sub(r'\bBOOLEAN\b', 'BOOLEAN', sql_pg, flags=re.IGNORECASE)
        sql_pg = re.sub(r'\bTEXT\b', 'TEXT', sql_pg, flags=re.IGNORECASE)
        sql_pg = re.sub(r'\bINTEGER\b(?!\s+PRIMARY)', 'INTEGER', sql_pg, flags=re.IGNORECASE)
        sql_pg = re.sub(r'\bROWID\b', 'id', sql_pg, flags=re.IGNORECASE)
        sql_pg = re.sub(r'LIMIT\s+-1', '', sql_pg, flags=re.IGNORECASE)  # SQLite "no limit"
        
        # Handle INSERT with node_type injection for cortex_nodes
        if cortex_table == 'cortex_nodes' and 'INSERT' in sql_pg.upper():
            node_type = self._infer_node_type(table)
            if node_type and 'node_type' not in sql_pg.lower():
                # Add node_type to the insert
                if 'VALUES' in sql_pg.upper():
                    cols_match = re.search(r'\(([^)]+)\)\s*VALUES', sql_pg, re.IGNORECASE)
                    if cols_match:
                        cols = cols_match.group(1)
                        sql_pg = sql_pg.replace(cols, cols + ', node_type', 1)
                        vals_match = re.search(r'VALUES\s*\(([^)]+)\)', sql_pg, re.IGNORECASE)
                        if vals_match:
                            vals = vals_match.group(1)
                            sql_pg = sql_pg.replace(vals, vals + f", '{node_type}'", 1)
                            if params:
                                params = list(params) + [node_type]
        
        return sql_pg, params
    
    def _infer_node_type(self, sqlite_table):
        """Map SQLite table name to cortex_nodes node_type."""
        type_map = {
            'distilled_tips': 'tip',
            'semantic_facts': 'fact',
            'episodic_memory': 'episode',
            'experiences': 'experience',
            'self_model': 'self_model',
            'identity_state': 'identity',
            'plans': 'plan',
            'propositions': 'proposition',
            'heuristics': 'heuristic',
            'meta_insights': 'meta_insight',
            'ideation_memory': 'ideation',
            'node_tree': 'node',
            'workspace': 'workspace',
            'session_outcomes': 'session',
            'action_history': 'action',
            'strategy_stats': 'strategy',
            'skills': 'skill',
            'skill_versions': 'skill_version',
            'experience_traces': 'trace',
            'recovery_strategies': 'recovery',
            'failure_cases': 'failure',
            'flow_nodes': 'flow_node',
            'retrieval_handles': 'handle',
            'circuit_breakers': 'circuit_breaker',
            'versions': 'version',
        }
        return type_map.get(sqlite_table.lower())
    
    def _store_generic(self, table, data):
        """Store data in the generic KV table for unmapped tables."""
        import json
        try:
            _ensure_kv_store(self._pg)
            with self._pg.cursor() as cur:
                cur.execute("""
                    INSERT INTO cortex_kv_store (table_name, data) VALUES (%s, %s)
                """, (table, json.dumps(data, default=str)))
            self._pg.commit()
            self._rowcount = cur.rowcount
            return True
        except Exception as e:
            logger.debug(f"KV store failed for {table}: {e}")
            return False
    
    def _insert_to_cortex(self, sqlite_table, data):
        """Insert parsed data into Cortex using the correct schema."""
        cortex_table = TABLE_MAP.get(sqlite_table.lower())
        if not cortex_table:
            return False
        
        try:
            if cortex_table == 'cortex_nodes':
                # Map SQLite columns → cortex_nodes columns
                node_type = self._infer_node_type(sqlite_table) or 'generic'
                import json
                metadata = {}
                core_fields = {'text', 'domain', 'confidence', 'node_type', 'elo',
                              'elo_matches', 'tags', 'is_active', 'provenance',
                              'trust', 'frequency', 'salience'}
                
                insert_data = {'node_type': node_type}
                for k, v in data.items():
                    if k in core_fields:
                        # Type guard: coerce numeric fields, reject timestamps in float fields
                        if k == 'confidence':
                            if isinstance(v, (int, float)):
                                fv = float(v)
                                # Detect Unix timestamps ( > 1e9 = year 2001+)
                                if fv > 1e9:
                                    v = 0.5  # Timestamp in confidence field — use default
                                else:
                                    v = min(max(fv, 0.0), 1.0)
                            else:
                                v = 0.5
                        elif k in ('elo', 'trust', 'salience') and isinstance(v, (int, float)):
                            v = float(v)
                        elif k in ('elo_matches', 'elo_wins', 'elo_losses', 'frequency', 'upvotes', 'downvotes', 'access_count'):
                            if isinstance(v, (int, float)):
                                v = int(v)
                            else:
                                v = 0
                        elif k == 'is_active':
                            v = bool(v) if isinstance(v, (int, float)) else True
                        insert_data[k] = v
                    else:
                        metadata[k] = v
                
                if metadata:
                    insert_data['metadata'] = json.dumps(metadata, default=str)
                if 'text' not in insert_data:
                    insert_data['text'] = json.dumps(data, default=str)[:500]
                
                cols = list(insert_data.keys())
                vals = list(insert_data.values())
                col_str = ', '.join(self._safe_col(c) for c in cols)
                placeholders = ', '.join(['%s'] * len(cols))
                
                self._pg_cur.execute(
                    f"INSERT INTO {self._safe_table('cortex_nodes')} ({col_str}) VALUES ({placeholders})",
                    vals
                )
                self._pg.commit()
                self._use_pg = True
                self._rowcount = self._pg_cur.rowcount
                return True
            
            elif cortex_table == 'cortex_eval_history':
                # Elo evaluation history
                import json
                cols = list(data.keys())
                # Map common SQLite column names to cortex_eval_history
                col_map = {'tip_id': 'node_id', 'winner_id': 'winner_id', 'loser_id': 'loser_id'}
                mapped_cols = [col_map.get(c, c) for c in cols]
                vals = list(data.values())
                col_str = ', '.join(self._safe_col(c) for c in mapped_cols)
                placeholders = ', '.join(['%s'] * len(mapped_cols))
                self._pg_cur.execute(
                    f"INSERT INTO {self._safe_table('cortex_eval_history')} ({col_str}) VALUES ({placeholders})",
                    vals
                )
                self._pg.commit()
                self._use_pg = True
                self._rowcount = self._pg_cur.rowcount
                return True
            
            else:
                # For other mapped tables, try direct insert with column mapping
                import json as _json
                # Predictions: map SQLite cols → Cortex cols + generate UUID
                if cortex_table == 'cortex_predictions':
                    pred_map = {
                        'prediction': 'task_summary',
                        'domain': 'task_type',
                        'timestamp': 'created_at',
                        'calibration_score': 'confidence',
                    }
                    mapped_data = {}
                    for k, v in data.items():
                        mapped_data[pred_map.get(k, k)] = v
                    # Generate UUID if not provided
                    if 'id' not in mapped_data:
                        import uuid
                        mapped_data['id'] = str(uuid.uuid4())
                    else:
                        # Ensure valid UUID format
                        try:
                            import uuid
                            mapped_data['id'] = str(uuid.UUID(str(mapped_data['id'])))
                        except ValueError:
                            import uuid
                            mapped_data['id'] = str(uuid.uuid4())
                    cols = list(mapped_data.keys())
                    vals = list(mapped_data.values())
                    col_str = ', '.join(self._safe_col(c) for c in cols)
                    placeholders = ', '.join(['%s'] * len(cols))
                    self._pg_cur.execute(
                        f"INSERT INTO {self._safe_table(cortex_table)} ({col_str}) VALUES ({placeholders})",
                        vals
                    )
                    self._pg.commit()
                    self._use_pg = True
                    self._rowcount = self._pg_cur.rowcount
                    return True
                # Generic: direct insert
                cols = list(data.keys())
                vals = list(data.values())
                col_str = ', '.join(self._safe_col(c) for c in cols)
                placeholders = ', '.join(['%s'] * len(cols))
                self._pg_cur.execute(
                    f"INSERT INTO {self._safe_table(cortex_table)} ({col_str}) VALUES ({placeholders})",
                    vals
                )
                self._pg.commit()
                self._use_pg = True
                self._rowcount = self._pg_cur.rowcount
                return True
        except Exception as e:
            logger.debug(f"Direct cortex insert failed for {sqlite_table}→{cortex_table}: {e}")
            try:
                self._pg.rollback()
            except:
                pass
        return False
    
    @staticmethod
    def _safe_col(col):
        """Validate a column name is safe for SQL (alphanumeric + underscore only)."""
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(col)):
            return str(col)
        raise ValueError(f"Invalid column name: {col!r}")
    
    @staticmethod
    def _safe_table(table):
        """Validate a table name is safe for SQL (alphanumeric + underscore only)."""
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(table)):
            return str(table)
        raise ValueError(f"Invalid table name: {table!r}")

    def _update_cortex(self, sqlite_table, data, sql, params):
        """UPDATE on Cortex for mapped tables."""
        cortex_table = TABLE_MAP.get(sqlite_table.lower())
        if not cortex_table:
            return False
        
        try:
            # Extract WHERE clause
            where_match = re.search(r'WHERE\s+(.+?)(?:;|$)', sql, re.IGNORECASE)
            where_clause = where_match.group(1).strip() if where_match else '1=1'
            where_clause = where_clause.replace('?', '%s')
            
            # Build SET clause
            set_parts = [f"{self._safe_col(k)} = %s" for k in data.keys()]
            set_clause = ', '.join(set_parts)
            
            # Extract WHERE params (params after SET params)
            set_param_count = len(data)
            where_params = list(params or [])[set_param_count:]
            all_params = list(data.values()) + where_params
            
            self._pg_cur.execute(
                f"UPDATE {self._safe_table(cortex_table)} SET {set_clause} WHERE {where_clause}",
                all_params
            )
            self._pg.commit()
            self._use_pg = True
            self._rowcount = self._pg_cur.rowcount
            return True
        except Exception as e:
            logger.debug(f"Cortex UPDATE failed for {sqlite_table}: {e}")
            try:
                self._pg.rollback()
            except:
                pass
            return False

    def execute(self, sql, params=None):
        """Execute SQL — routes to Cortex, KV store, or SQLite fallback."""
        sql = sql.strip()
        sql_upper = sql.upper()
        table = self._extract_table(sql)
        
        # ── CREATE TABLE → skip (tables exist in Cortex or KV store) ──
        if sql_upper.startswith('CREATE'):
            self._rowcount = 0
            self._description = None
            return self
        
        # ── Mapped table → route to Cortex ──
        if table and self._is_mapped(table):
            
            # INSERT → parse and insert via schema-aware method
            if sql_upper.startswith('INSERT') or sql_upper.startswith('REPLACE'):
                data = self._parse_sql_to_dict(sql, params)
                if data and self._insert_to_cortex(table, data):
                    return self
                # Fall through to SQLite fallback
            
            # UPDATE → parse and update via schema-aware method
            elif sql_upper.startswith('UPDATE'):
                data = self._parse_sql_to_dict(sql, params)
                if data and self._update_cortex(table, data, sql, params):
                    return self
                # Fall through to SQLite fallback
            
            # DELETE → translate WHERE clause + inject node_type filter for cortex_nodes
            elif sql_upper.startswith('DELETE'):
                cortex_table = TABLE_MAP[table.lower()]
                where_match = re.search(r'WHERE\s+(.+?)(?:;|$)', sql, re.IGNORECASE)
                where_clause = where_match.group(1).replace('?', '%s') if where_match else '1=1'
                
                # For cortex_nodes, inject node_type filter (same as SELECT)
                extra_params = []
                if cortex_table == 'cortex_nodes':
                    node_type = self._infer_node_type(table)
                    if node_type:
                        if 'WHERE' in where_clause.upper():
                            where_clause = f"node_type = %s AND {where_clause}"
                        else:
                            where_clause = f"node_type = %s"
                        extra_params = [node_type]
                    # Remap condition/recommendation in WHERE
                    where_clause = where_clause.replace('condition', "metadata->>'condition'")
                    where_clause = where_clause.replace('recommendation', "metadata->>'recommendation'")
                
                try:
                    self._pg_cur.execute(
                        f"DELETE FROM {self._safe_table(cortex_table)} WHERE {where_clause}",
                        tuple(extra_params) + tuple(params or ())
                    )
                    self._pg.commit()
                    self._use_pg = True
                    self._rowcount = self._pg_cur.rowcount
                    return self
                except Exception as e:
                    logger.debug(f"Cortex DELETE failed: {e}")
                    try: self._pg.rollback()
                    except: pass
            
            # SELECT → translate table name + WHERE clause + inject node_type filter
            elif sql_upper.startswith('SELECT'):
                cortex_table = TABLE_MAP[table.lower()]
                # Word-boundary regex replacement (avoids double-replacement when
                # cortex_table contains the original table name as substring,
                # e.g. predictions → cortex_predictions)
                sql_pg = re.sub(
                    r'\b' + re.escape(table) + r'\b',
                    cortex_table, sql, count=0, flags=re.IGNORECASE
                )
                sql_pg = sql_pg.replace('?', '%s')
                
                # For cortex_nodes, inject node_type filter + remap columns
                if cortex_table == 'cortex_nodes':
                    node_type = self._infer_node_type(table)
                    if node_type:
                        if 'WHERE' in sql_pg.upper():
                            # Parameterized to prevent SQL injection
                            sql_pg = re.sub(r'(?i)WHERE', "WHERE node_type = %s AND", sql_pg, count=1)
                            params = (node_type,) + tuple(params or ())
                        else:
                            # No WHERE clause — add one before ORDER/LIMIT/GROUP
                            insert_pos = len(sql_pg)
                            for kw in ['ORDER BY', 'LIMIT', 'GROUP BY']:
                                m = re.search(kw, sql_pg, re.IGNORECASE)
                                if m:
                                    insert_pos = m.start()
                                    break
                            # Parameterized WHERE to prevent SQL injection
                            sql_pg = sql_pg[:insert_pos].rstrip() + " WHERE node_type = %s " + sql_pg[insert_pos:]
                            params = (node_type,) + tuple(params or ())
                    
                    # Remap SQLite column names → cortex_nodes columns
                    # SQLite distilled_tips cols not in cortex_nodes:
                    #   condition, recommendation, tip_type, rationale, source_ids
                    # In cortex_nodes they live in metadata JSONB.
                    # 
                    # BUG FIX (Apr 15): condition/recommendation were merged into `text` 
                    # during migration for ~78% of tips (IF...THEN format). Only 22% have
                    # them in metadata. The remap now tries metadata first, then extracts
                    # from text using regex as fallback.
                    #
                    # For condition: IF text is "IF <cond> THEN <rec>", extract <cond>
                    # For recommendation: extract everything after THEN
                    # For WHERE condition LIKE ? / condition = ?: also match against text
                    _col_remap = [
                        ('condition', (
                            "COALESCE("
                            "  metadata->>'condition', "
                            "  CASE WHEN text ~* '^IF\\s+' THEN "
                            "    regexp_replace("
                            "      substring(text from '(?i)^IF\\s+(.+?)\\s+THEN'), "
                            "      '\\s+$', ''"
                            "    ) "
                            "  ELSE '' END, "
                            "  ''"
                            ")"
                        )),
                        ('recommendation', (
                            "COALESCE("
                            "  metadata->>'recommendation', "
                            "  CASE WHEN text ~* '^IF\\s+' AND text ~* '\\s+THEN\\s+' THEN "
                            "    substring(text from '(?i)\\s+THEN\\s+(.+)') "
                            "  ELSE '' END, "
                            "  ''"
                            ")"
                        )),
                        ('tip_type', "COALESCE(metadata->>'tip_type', '')"),
                        ('rationale', "COALESCE(metadata->>'rationale', '')"),
                        ('source_ids', "COALESCE(metadata->>'source_ids', COALESCE(source_ids, ''))"),
                    ]
                    for _old, _new in _col_remap:
                        # Only match if NOT preceded by > (already remapped)
                        # Use re.escape on replacement to avoid interpreting SQL as regex
                        sql_pg = re.sub(
                            r'(?<!>)(?<!\w)\b' + _old + r'\b',
                            lambda m: _new, sql_pg, flags=re.IGNORECASE
                        )
                    
                    # WHERE clause expansion: when condition/recommendation appear in WHERE
                    # with LIKE/=, also search the text field (since 78% of tips store
                    # condition/rec in text, not metadata). 
                    # e.g. "WHERE COALESCE(metadata->>'condition',...) LIKE %s"
                    #   becomes "WHERE (COALESCE(...) LIKE %s OR text ILIKE %s)"
                    if re.search(r"metadata->>'condition'", sql_pg):
                        sql_pg = re.sub(
                            r"(COALESCE\(metadata->>'condition'.*?\))\s*(LIKE|ILIKE|=)\s*(%s)",
                            r"(\1 \2 \3 OR text ILIKE %3$s)",
                            sql_pg, flags=re.IGNORECASE
                        )
                    if re.search(r"metadata->>'recommendation'", sql_pg):
                        sql_pg = re.sub(
                            r"(COALESCE\(metadata->>'recommendation'.*?\))\s*(LIKE|ILIKE|=)\s*(%s)",
                            r"(\1 \2 \3 OR text ILIKE %3$s)",
                            sql_pg, flags=re.IGNORECASE
                        )
                
                # For cortex_predictions, remap SQLite columns → PG columns
                elif cortex_table == 'cortex_predictions':
                    _pred_col_remap = [
                        ('timestamp', 'created_at'),
                        ('calibration_score', 'confidence'),
                        ('iteration_error', 'difficulty_error'),
                        ('prediction', 'task_summary'),
                        ('domain', 'task_type'),
                    ]
                    for _old, _new in _pred_col_remap:
                        sql_pg = re.sub(
                            r'(?<!\w)\b' + _old + r'\b',
                            _new, sql_pg, flags=re.IGNORECASE
                        )
                    # SQLite 0/1 → PG boolean for resolved column
                    sql_pg = re.sub(r'\bresolved\s*=\s*0\b', 'resolved = false', sql_pg, flags=re.IGNORECASE)
                    sql_pg = re.sub(r'\bresolved\s*=\s*1\b', 'resolved = true', sql_pg, flags=re.IGNORECASE)
                    sql_pg = re.sub(r'\bresolved\s*=\s*\?\b', 'resolved = %s', sql_pg, flags=re.IGNORECASE)
                
                try:
                    self._pg_cur.execute(sql_pg, params or ())
                    self._use_pg = True
                    self._rowcount = self._pg_cur.rowcount
                    self._description = self._pg_cur.description
                    return self
                except Exception as e:
                    logger.debug(f"Cortex SELECT failed for {table}: {e}")
                    try: self._pg.rollback()
                    except: pass
                    # Fall through to SQLite
        
        # ── Unmapped table → KV store for writes, SQLite for reads ──
        if table and not self._is_mapped(table) and self._pg:
            if sql_upper.startswith('INSERT') or sql_upper.startswith('UPDATE') or sql_upper.startswith('REPLACE'):
                try:
                    data = self._parse_sql_to_dict(sql, params)
                    if data:
                        self._store_generic(table, data)
                        return self
                except:
                    pass
            elif sql_upper.startswith('SELECT'):
                try:
                    import json
                    _ensure_kv_store(self._pg)
                    with self._pg.cursor() as cur:
                        cur.execute("SELECT data FROM cortex_kv_store WHERE table_name = %s ORDER BY created_at DESC LIMIT 1000", (table,))
                        rows = cur.fetchall()
                        if rows:
                            self._last_rows = [r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in rows]
                            self._rowcount = len(self._last_rows)
                            self._use_pg = True
                            if self._last_rows:
                                keys = list(self._last_rows[0].keys())
                                self._description = [(k, None, None, None, None, None, None) for k in keys]
                            return self
                except:
                    pass
        
        # ── Final fallback: SQLite ──
        sqlite_cur = self._fallback_sqlite()
        if sqlite_cur:
            try:
                sqlite_cur.execute(sql, params or ())
                self._use_pg = False
                self._rowcount = sqlite_cur.rowcount
                self._description = sqlite_cur.description
                return self
            except Exception as e:
                logger.debug(f"SQLite fallback also failed: {e}")
        
        # Nothing worked
        self._rowcount = 0
        self._description = None
        return self
    
    def _parse_sql_to_dict(self, sql, params):
        """Best-effort parse SQL INSERT/UPDATE to dict."""
        sql_upper = sql.upper()
        data = {}
        
        if sql_upper.startswith('INSERT'):
            cols_match = re.search(r'\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)', sql, re.IGNORECASE)
            if cols_match:
                cols = [c.strip().strip('"') for c in cols_match.group(1).split(',')]
                if params:
                    for i, col in enumerate(cols):
                        data[col] = params[i] if i < len(params) else None
        elif sql_upper.startswith('UPDATE'):
            # Extract SET col = val pairs
            sets = re.findall(r'(\w+)\s*=\s*\?', sql, re.IGNORECASE)
            if params:
                for i, col in enumerate(sets):
                    data[col] = params[i] if i < len(params) else None
        
        return data if data else None
    
    def fetchone(self):
        if self._use_pg:
            try:
                r = self._pg_cur.fetchone()
                if r and hasattr(r, '_asdict'):
                    return tuple(r._asdict().values())
                return r
            except:
                pass
        if self._sqlite_cur:
            return self._sqlite_cur.fetchone()
        if self._last_rows:
            r = self._last_rows.pop(0)
            if isinstance(r, dict):
                return tuple(r.values())
            return r
        return None
    
    def fetchall(self):
        if self._use_pg:
            try:
                rows = self._pg_cur.fetchall()
                if rows and hasattr(rows[0], '_asdict'):
                    return [tuple(r._asdict().values()) for r in rows]
                return rows
            except:
                pass
        if self._sqlite_cur:
            return self._sqlite_cur.fetchall()
        result = self._last_rows[:]
        self._last_rows = []
        if result and isinstance(result[0], dict):
            return [tuple(r.values()) for r in result]
        return result
    
    def fetchmany(self, size=None):
        if self._use_pg:
            try:
                return self._pg_cur.fetchmany(size or 1)
            except:
                pass
        if self._sqlite_cur:
            return self._sqlite_cur.fetchmany(size or 1)
        return []
    
    @property
    def rowcount(self):
        return self._rowcount
    
    @rowcount.setter
    def rowcount(self, val):
        self._rowcount = val
    
    @property
    def description(self):
        return self._description
    
    @description.setter
    def description(self, val):
        self._description = val
    
    @property
    def lastrowid(self):
        if self._pg_cur and hasattr(self._pg_cur, 'lastrowid'):
            return self._pg_cur.lastrowid
        return None
    
    def close(self):
        try:
            self._pg_cur.close()
        except:
            pass
        if self._sqlite_cur:
            try:
                self._sqlite_cur.close()
            except:
                pass
    
    def __iter__(self):
        rows = self.fetchall()
        return iter(rows)
    
    def executescript(self, sql_script):
        """Handle CREATE TABLE scripts — just ignore for mapped tables."""
        # Split on semicolons, execute each
        for stmt in sql_script.split(';'):
            stmt = stmt.strip()
            if stmt:
                self.execute(stmt)
        return self
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class CortexConnection:
    """Mimics sqlite3.Connection but routes to Cortex PostgreSQL.
    Falls back to real SQLite for anything Cortex can't handle."""
    
    def __init__(self, db_path=':memory:', **kwargs):
        self._pg = _get_pg_conn()
        # Use ORIGINAL sqlite3.connect (before monkey-patch) to avoid recursion
        self._sqlite = _ORIGINAL_CONNECT(db_path, **kwargs)
        self._sqlite.row_factory = None  # Return tuples, not Row objects
        self._closed = False
        self._db_path = db_path
        
        if self._pg:
            _ensure_kv_store(self._pg)
            logger.debug(f"CortexConnection: Postgres + SQLite ({db_path})")
        else:
            logger.warning(f"CortexConnection: Postgres DOWN, SQLite only ({db_path})")
    
    def cursor(self):
        return CortexCursor(self._pg, self._sqlite)
    
    def commit(self):
        if self._pg:
            try:
                self._pg.commit()
            except Exception as e:
                logger.debug(f"PG commit failed: {e}")
        if self._sqlite:
            try:
                self._sqlite.commit()
            except:
                pass
    
    def rollback(self):
        if self._pg:
            try:
                self._pg.rollback()
            except:
                pass
        if self._sqlite:
            try:
                self._sqlite.rollback()
            except:
                pass
    
    def close(self):
        self._closed = True
        if self._pg:
            try:
                self._pg.close()
            except:
                pass
        if self._sqlite:
            try:
                self._sqlite.close()
            except:
                pass
    
    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur
    
    def executemany(self, sql, params_list):
        for params in params_list:
            self.execute(sql, params)
    
    def executescript(self, sql_script):
        cur = self.cursor()
        cur.executescript(sql_script)
    
    @property
    def row_factory(self):
        return None
    
    @row_factory.setter
    def row_factory(self, val):
        pass  # Ignore — always return tuples
    
    @property
    def total_changes(self):
        if self._sqlite:
            return self._sqlite.total_changes
        return 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    @property
    def in_transaction(self):
        if self._pg:
            return not self._pg.autocommit
        return False


def connect(db_path=':memory:', **kwargs):
    """
    Drop-in replacement for sqlite3.connect().
    Routes to Cortex PostgreSQL with SQLite fallback.
    """
    # Only intercept cerebrum_memory.db connections
    path_str = str(db_path)
    if 'cerebrum' in path_str.lower() or 'hindsight' in path_str.lower():
        return CortexConnection(db_path, **kwargs)
    
    # For any other DB, just use regular SQLite
    return _ORIGINAL_CONNECT(db_path, **kwargs)


def patch_sqlite3():
    """
    Monkey-patch sqlite3.connect globally.
    Call this once at startup to intercept ALL sqlite3.connect() calls.
    
    Usage in brain.py or meta_loop.py:
        from cortex_compat_shim import patch_sqlite3
        patch_sqlite3()  # Now all sqlite3.connect() routes through Cortex
    """
    import sqlite3 as _sqlite3
    # Use the module-level saved original, not a new local
    _orig = _ORIGINAL_CONNECT
    
    def _patched_connect(db_path=':memory:', **kwargs):
        path_str = str(db_path)
        if 'cerebrum' in path_str.lower() or 'hindsight' in path_str.lower():
            return CortexConnection(db_path, **kwargs)
        return _orig(db_path, **kwargs)
    
    _sqlite3.connect = _patched_connect
    logger.info("sqlite3.connect() patched → Cortex proxy active")


# ── Test ──
if __name__ == "__main__":
    print("Testing Cortex Shim...")
    conn = connect(str(Path.home() / '.hermes/cerebrum_memory.db'))
    cur = conn.cursor()
    
    # Test read from distilled_tips
    cur.execute("SELECT COUNT(*) FROM distilled_tips")
    count = cur.fetchone()
    print(f"  distilled_tips count: {count}")
    
    # Test SELECT
    cur.execute("SELECT * FROM distilled_tips LIMIT 3")
    rows = cur.fetchall()
    print(f"  Sample rows: {len(rows)}")
    for r in rows[:2]:
        if isinstance(r, (tuple, list)):
            print(f"    {str(r)[:100]}")
    
    conn.close()
    print("Done!")
