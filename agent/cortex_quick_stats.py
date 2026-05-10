#!/usr/bin/env python3
"""Quick Cortex DB stats — always accurate, always uses column-based queries."""
import psycopg2, psycopg2.extras, json, sys

def get_accurate_stats():
    conn = psycopg2.connect('postgresql://hindsight:hindsight@localhost:5432/cortex')
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Node counts
    cur.execute("SELECT node_type, count(*) as c, count(*) FILTER (WHERE elo != 1200.0) as elo_custom, round(avg(elo)::numeric,1) as avg_elo, sum(elo_matches) as total_matches FROM cortex_nodes WHERE is_active = TRUE GROUP BY node_type ORDER BY c DESC")
    types = [dict(r) for r in cur.fetchall()]
    
    # Totals
    cur.execute("SELECT count(*) as c FROM cortex_nodes WHERE is_active = TRUE")
    total = cur.fetchone()['c']
    cur.execute("SELECT count(*) as c FROM cortex_nodes WHERE is_active = FALSE")
    inactive = cur.fetchone()['c']
    
    # Embeddings
    cur.execute("SELECT count(*) as c FROM cortex_nodes WHERE embedding IS NOT NULL")
    with_emb = cur.fetchone()['c']
    
    # Tip Elo specifics
    cur.execute("SELECT count(*) as c FROM cortex_nodes WHERE node_type='tip' AND is_active = TRUE")
    total_tips = cur.fetchone()['c']
    cur.execute("SELECT count(*) as c FROM cortex_nodes WHERE node_type='tip' AND is_active = TRUE AND elo_matches > 0")
    rated_tips = cur.fetchone()['c']
    cur.execute("SELECT min(elo) as mn, max(elo) as mx, round(avg(elo)::numeric,1) as avg, round(stddev(elo)::numeric,1) as sd FROM cortex_nodes WHERE node_type='tip' AND is_active = TRUE")
    elo_stats = dict(cur.fetchone())
    
    # DB size
    cur.execute("SELECT pg_size_pretty(pg_database_size('cortex')) as size")
    db_size = cur.fetchone()['size']
    
    # Dead tuples
    cur.execute("SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname='cortex_nodes'")
    dead = cur.fetchone()
    dead_tup = dead['n_dead_tup'] if dead else 0
    
    # Flywheel activity (last 24h)
    cur.execute("SELECT cycle_type, count(*) as c, sum(items_produced) as produced FROM cortex_flywheel WHERE started_at > NOW() - INTERVAL '24 hours' GROUP BY cycle_type")
    fw = [dict(r) for r in cur.fetchall()]
    
    # Last daemon heartbeat (most recent updated_at on tips)
    cur.execute("SELECT max(updated_at) as last_update FROM cortex_nodes WHERE node_type='tip'")
    last_update = cur.fetchone()['last_update']
    
    conn.close()
    
    pct_rated = (rated_tips / total_tips * 100) if total_tips > 0 else 0
    pct_emb = (with_emb / total * 100) if total > 0 else 0
    
    return {
        'total_active': total,
        'total_inactive': inactive,
        'db_size': db_size,
        'dead_tuples': dead_tup,
        'embedding_pct': round(pct_emb, 1),
        'types': {t['node_type']: {'count': t['c'], 'avg_elo': float(t['avg_elo']) if t['avg_elo'] else 0, 'total_matches': t['total_matches'] or 0} for t in types},
        'tips': {
            'total': total_tips,
            'rated': rated_tips,
            'pct_rated': round(pct_rated, 1),
            'elo_min': float(elo_stats['mn']) if elo_stats['mn'] else 0,
            'elo_max': float(elo_stats['mx']) if elo_stats['mx'] else 0,
            'elo_avg': float(elo_stats['avg']) if elo_stats['avg'] else 0,
            'elo_std': float(elo_stats['sd']) if elo_stats['sd'] else 0,
        },
        'flywheel_24h': fw,
        'last_tip_update': str(last_update) if last_update else 'never',
    }

if __name__ == '__main__':
    stats = get_accurate_stats()
    print(json.dumps(stats, indent=2, default=str))
