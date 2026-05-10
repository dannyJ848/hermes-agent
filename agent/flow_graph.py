#!/usr/bin/env python3
"""
Flow Graph Builder — Data/Control flow analysis for codebases.
Extends code_intelligence.py AST chunking with actual flow understanding.

Based on: RepoGraph (SWE-bench top performer), tree-sitter dataflow analysis.
Builds a directed graph of: definitions → uses → callers → callees.

DB: ~/.hermes/code_intelligence.db (adds flow_edges + flow_nodes tables)
"""

import os
import sys
import json
import sqlite3
import hashlib
import time
from pathlib import Path
from collections import defaultdict

DB_PATH = os.path.expanduser("~/.hermes/code_intelligence.db")

# Language-specific tree-sitter queries
# We use regex fallback when tree-sitter isn't available
PYTHON_PATTERNS = {
    "def": r'def\s+(\w+)\s*\(([^)]*)\)',
    "class": r'class\s+(\w+)',
    "import": r'^(?:from\s+(\S+)\s+)?import\s+(.+?)$',
    "call": r'(\w+)\s*\(',
    "assign": r'(\w+)\s*=\s*',
    "return": r'return\s+(.+?)$',
}

TS_PATTERNS = {
    "function": r'(?:function|const|let|var)\s+(\w+)\s*(?:=\s*)?(?:\(|<)',
    "class": r'class\s+(\w+)',
    "import": r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]',
    "call": r'(\w+)\s*\(',
    "export": r'export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)',
}


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("CREATE TABLE IF NOT EXISTS flow_nodes ("
               "node_id TEXT PRIMARY KEY, "
               "repo TEXT, file TEXT, name TEXT, node_type TEXT, "
               "signature TEXT, line_start INTEGER, line_end INTEGER, "
               "language TEXT, updated REAL)")
    db.execute("CREATE TABLE IF NOT EXISTS flow_edges ("
               "edge_id TEXT PRIMARY KEY, "
               "source_node TEXT, target_node TEXT, edge_type TEXT, "
               "repo TEXT, weight REAL DEFAULT 1.0, updated REAL)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_flow_nodes_repo ON flow_nodes(repo, name)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_flow_edges_source ON flow_edges(source_node)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_flow_edges_target ON flow_edges(target_node)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_flow_edges_type ON flow_edges(edge_type)")
    db.commit()
    return db


def detect_language(filepath):
    ext = Path(filepath).suffix.lower()
    mapping = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.tsx': 'typescript', '.jsx': 'javascript',
        '.rs': 'rust', '.go': 'go', '.java': 'java',
        '.cpp': 'cpp', '.c': 'c', '.h': 'c',
        '.rb': 'ruby', '.php': 'php', '.swift': 'swift',
    }
    return mapping.get(ext, 'unknown')


def make_node_id(repo, filepath, name, node_type):
    raw = f"{repo}:{filepath}:{name}:{node_type}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def make_edge_id(source, target, edge_type):
    raw = f"{source}->{target}:{edge_type}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def extract_python_definitions(content, filepath, repo):
    """Extract functions, classes, imports, calls from Python."""
    import re
    nodes = []
    edges = []
    
    lines = content.split('\n')
    current_class = None
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Class definition
        m = re.match(r'class\s+(\w+)', stripped)
        if m:
            current_class = m.group(1)
            node_id = make_node_id(repo, filepath, current_class, 'class')
            nodes.append({
                'node_id': node_id, 'repo': repo, 'file': filepath,
                'name': current_class, 'node_type': 'class',
                'signature': stripped, 'line_start': i, 'line_end': i,
                'language': 'python'
            })
            continue
        
        # Dedent = leaving class
        if line and not line[0].isspace() and current_class and not stripped.startswith('class'):
            current_class = None
        
        # Function definition
        m = re.match(r'def\s+(\w+)\s*\(([^)]*)\)', stripped)
        if m:
            fname = m.group(1)
            params = m.group(2)
            full_name = f"{current_class}.{fname}" if current_class else fname
            node_id = make_node_id(repo, filepath, full_name, 'function')
            nodes.append({
                'node_id': node_id, 'repo': repo, 'file': filepath,
                'name': full_name, 'node_type': 'function',
                'signature': f"def {full_name}({params})",
                'line_start': i, 'line_end': i,
                'language': 'python'
            })
            
            # Class-contains-function edge
            if current_class:
                class_node = make_node_id(repo, filepath, current_class, 'class')
                edge_id = make_edge_id(class_node, node_id, 'contains')
                edges.append({
                    'edge_id': edge_id, 'source_node': class_node,
                    'target_node': node_id, 'edge_type': 'contains',
                    'repo': repo
                })
            
            # Parse params for calls
            for param in params.split(','):
                param = param.strip().split('=')[0].strip()
                if param and param not in ('self', 'cls', '*args', '**kwargs'):
                    # Parameter definition
                    pass
            
            continue
        
        # Function call
        calls = re.findall(r'(\w+)\s*\(', stripped)
        for callee in calls:
            if callee in ('if', 'for', 'while', 'with', 'return', 'print', 'def', 'class'):
                continue
            if current_class:
                caller = f"{current_class}.<method>"  # approximate
            else:
                caller = "<module>"
            
            # Edge: caller -> callee (will be resolved to node_ids later)
            caller_id = make_node_id(repo, filepath, caller, 'scope')
            callee_id = make_node_id(repo, '', callee, 'function')  # may be in different file
            edge_id = make_edge_id(caller_id, callee_id, 'calls')
            edges.append({
                'edge_id': edge_id, 'source_node': caller_id,
                'target_node': callee_id, 'edge_type': 'calls',
                'repo': repo
            })
        
        # Import
        m = re.match(r'from\s+(\S+)\s+import\s+(.+)', stripped)
        if m:
            module = m.group(1)
            imported = [x.strip() for x in m.group(2).split(',')]
            for imp in imported:
                imp = imp.split(' as ')[0].strip()
                if imp:
                    src_id = make_node_id(repo, module.replace('.', '/'), imp, 'function')
                    tgt_id = make_node_id(repo, filepath, imp, 'import')
                    edge_id = make_edge_id(tgt_id, src_id, 'imports')
                    edges.append({
                        'edge_id': edge_id, 'source_node': tgt_id,
                        'target_node': src_id, 'edge_type': 'imports',
                        'repo': repo
                    })
            continue
        
        m = re.match(r'import\s+(\S+)', stripped)
        if m:
            module = m.group(1).split(' as ')[0]
            src_id = make_node_id(repo, module.replace('.', '/'), '*', 'module')
            tgt_id = make_node_id(repo, filepath, module, 'import')
            edge_id = make_edge_id(tgt_id, src_id, 'imports')
            edges.append({
                'edge_id': edge_id, 'source_node': tgt_id,
                'target_node': src_id, 'edge_type': 'imports',
                'repo': repo
            })
    
    return nodes, edges


def extract_ts_definitions(content, filepath, repo):
    """Extract functions, classes, imports from TS/JS."""
    import re
    nodes = []
    edges = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Function/const/let/var declaration
        m = re.match(r'(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)', stripped)
        if not m:
            m = re.match(r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::\s*[^=]+)?\s*=\s*(?:async\s+)?(?:\(|function)', stripped)
        if m:
            name = m.group(1)
            node_id = make_node_id(repo, filepath, name, 'function')
            nodes.append({
                'node_id': node_id, 'repo': repo, 'file': filepath,
                'name': name, 'node_type': 'function',
                'signature': stripped[:100], 'line_start': i, 'line_end': i,
                'language': 'typescript'
            })
            continue
        
        # Class
        m = re.match(r'(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)', stripped)
        if m:
            name = m.group(1)
            node_id = make_node_id(repo, filepath, name, 'class')
            nodes.append({
                'node_id': node_id, 'repo': repo, 'file': filepath,
                'name': name, 'node_type': 'class',
                'signature': stripped[:100], 'line_start': i, 'line_end': i,
                'language': 'typescript'
            })
            continue
        
        # Import
        m = re.match(r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]', stripped)
        if m:
            module = m.group(1)
            edge_id = make_edge_id(
                make_node_id(repo, filepath, Path(filepath).stem, 'module'),
                make_node_id(repo, module, '*', 'module'),
                'imports'
            )
            edges.append({
                'edge_id': edge_id,
                'source_node': make_node_id(repo, filepath, Path(filepath).stem, 'module'),
                'target_node': make_node_id(repo, module, '*', 'module'),
                'edge_type': 'imports', 'repo': repo
            })
    
    return nodes, edges


def index_file(filepath, repo, db):
    """Index a single file into the flow graph."""
    lang = detect_language(filepath)
    if lang == 'unknown':
        return 0, 0
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        return 0, 0
    
    if lang == 'python':
        nodes, edges = extract_python_definitions(content, filepath, repo)
    elif lang in ('typescript', 'javascript'):
        nodes, edges = extract_ts_definitions(content, filepath, repo)
    else:
        return 0, 0
    
    now = time.time()
    for n in nodes:
        n['updated'] = now
        db.execute("INSERT OR REPLACE INTO flow_nodes "
                   "(node_id, repo, file, name, node_type, signature, line_start, line_end, language, updated) "
                   "VALUES (:node_id, :repo, :file, :name, :node_type, :signature, :line_start, :line_end, :language, :updated)",
                   n)
    
    for e in edges:
        e['updated'] = now
        db.execute("INSERT OR REPLACE INTO flow_edges "
                   "(edge_id, source_node, target_node, edge_type, repo, weight, updated) "
                   "VALUES (:edge_id, :source_node, :target_node, :edge_type, :repo, 1.0, :updated)",
                   e)
    
    return len(nodes), len(edges)


def index_repo(repo_path, repo_name=None, db=None):
    """Index an entire repository."""
    if db is None:
        db = get_db()
    if repo_name is None:
        repo_name = os.path.basename(repo_path)
    
    total_nodes = 0
    total_edges = 0
    file_count = 0
    
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist',
                 'build', '.next', '.turbo', 'coverage', '.cache', 'target'}
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in ('.py', '.js', '.ts', '.tsx', '.jsx', '.rs', '.go', '.java'):
                filepath = os.path.join(root, f)
                relpath = os.path.relpath(filepath, repo_path)
                n, e = index_file(filepath, repo_name, db)
                total_nodes += n
                total_edges += e
                file_count += 1
    
    db.commit()
    return {'files': file_count, 'nodes': total_nodes, 'edges': total_edges}


def get_callers(name, repo=None, db=None):
    """Find all callers of a function/class."""
    if db is None:
        db = get_db()
    
    # Find the node
    if repo:
        nodes = db.execute("SELECT * FROM flow_nodes WHERE name=? AND repo=?",
                          (name, repo)).fetchall()
    else:
        nodes = db.execute("SELECT * FROM flow_nodes WHERE name=?", (name,)).fetchall()
    
    results = []
    for node in nodes:
        node_id = node[0]  # node_id is first column
        # Find edges pointing TO this node
        edges = db.execute("SELECT e.*, ns.name, ns.file "
                          "FROM flow_edges e "
                          "JOIN flow_nodes ns ON e.source_node = ns.node_id "
                          "WHERE e.target_node=? AND e.edge_type='calls'",
                          (node_id,)).fetchall()
        for edge in edges:
            results.append({
                'caller': edge[7],  # ns.name
                'file': edge[8],    # ns.file
                'callee': name
            })
    
    return results


def get_callees(name, repo=None, db=None):
    """Find all functions called by a function/class."""
    if db is None:
        db = get_db()
    
    if repo:
        nodes = db.execute("SELECT * FROM flow_nodes WHERE name=? AND repo=?",
                          (name, repo)).fetchall()
    else:
        nodes = db.execute("SELECT * FROM flow_nodes WHERE name=?", (name,)).fetchall()
    
    results = []
    for node in nodes:
        node_id = node[0]
        edges = db.execute("SELECT e.*, nt.name, nt.file "
                          "FROM flow_edges e "
                          "JOIN flow_nodes nt ON e.target_node = nt.node_id "
                          "WHERE e.source_node=? AND e.edge_type='calls'",
                          (node_id,)).fetchall()
        for edge in edges:
            results.append({
                'callee': edge[7],
                'file': edge[8],
                'caller': name
            })
    
    return results


def get_import_graph(repo, db=None):
    """Get the full import dependency graph for a repo."""
    if db is None:
        db = get_db()
    
    edges = db.execute("SELECT e.source_node, e.target_node, n1.file, n2.file "
                      "FROM flow_edges e "
                      "JOIN flow_nodes n1 ON e.source_node = n1.node_id "
                      "JOIN flow_nodes n2 ON e.target_node = n2.node_id "
                      "WHERE e.repo=? AND e.edge_type='imports'",
                      (repo,)).fetchall()
    
    return [{'from_file': e[2], 'to_module': e[3], 'from_node': e[0], 'to_node': e[1]}
            for e in edges]


def get_impact_analysis(filepath, repo, db=None):
    """Analyze what would be affected by changing a file.
    Returns files/functions that depend on definitions in the given file."""
    if db is None:
        db = get_db()
    
    # Get all nodes defined in this file
    nodes = db.execute("SELECT node_id, name, node_type FROM flow_nodes "
                      "WHERE file LIKE ? AND repo=?",
                      (f'%{filepath}%', repo)).fetchall()
    
    impacted = []
    for node_id, name, node_type in nodes:
        # Find all edges referencing this node
        callers = db.execute("SELECT n.name, n.file, n.node_type "
                            "FROM flow_edges e "
                            "JOIN flow_nodes n ON e.source_node = n.node_id "
                            "WHERE e.target_node=?", (node_id,)).fetchall()
        for caller_name, caller_file, caller_type in callers:
            impacted.append({
                'changed': name,
                'changed_type': node_type,
                'impacted': caller_name,
                'impacted_file': caller_file,
                'impacted_type': caller_type
            })
    
    return impacted


def stats(db=None):
    """Get flow graph statistics."""
    if db is None:
        db = get_db()
    
    n_nodes = db.execute("SELECT COUNT(*) FROM flow_nodes").fetchone()[0]
    n_edges = db.execute("SELECT COUNT(*) FROM flow_edges").fetchone()[0]
    repos = db.execute("SELECT DISTINCT repo FROM flow_nodes").fetchall()
    
    by_type = {}
    for t in ('function', 'class', 'import', 'scope', 'module'):
        count = db.execute("SELECT COUNT(*) FROM flow_nodes WHERE node_type=?", (t,)).fetchone()[0]
        if count > 0:
            by_type[t] = count
    
    by_edge = {}
    for t in ('calls', 'imports', 'contains'):
        count = db.execute("SELECT COUNT(*) FROM flow_edges WHERE edge_type=?", (t,)).fetchone()[0]
        if count > 0:
            by_edge[t] = count
    
    return {
        'nodes': n_nodes,
        'edges': n_edges,
        'repos': [r[0] for r in repos],
        'node_types': by_type,
        'edge_types': by_edge
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: flow_graph.py <command> [args]'}))
        sys.exit(1)
    
    cmd = sys.argv[1]
    db = get_db()
    
    if cmd == 'index':
        repo_path = sys.argv[2]
        repo_name = sys.argv[3] if len(sys.argv) > 3 else None
        result = index_repo(repo_path, repo_name, db)
        print(json.dumps(result))
    
    elif cmd == 'callers':
        name = sys.argv[2]
        repo = sys.argv[3] if len(sys.argv) > 3 else None
        result = get_callers(name, repo, db)
        print(json.dumps(result, indent=2))
    
    elif cmd == 'callees':
        name = sys.argv[2]
        repo = sys.argv[3] if len(sys.argv) > 3 else None
        result = get_callees(name, repo, db)
        print(json.dumps(result, indent=2))
    
    elif cmd == 'impact':
        filepath = sys.argv[2]
        repo = sys.argv[3] if len(sys.argv) > 3 else None
        result = get_impact_analysis(filepath, repo, db)
        print(json.dumps(result, indent=2))
    
    elif cmd == 'imports':
        repo = sys.argv[2]
        result = get_import_graph(repo, db)
        print(json.dumps(result, indent=2))
    
    elif cmd == 'stats':
        result = stats(db)
        print(json.dumps(result, indent=2))
    
    else:
        print(json.dumps({'error': f'Unknown command: {cmd}'}))
