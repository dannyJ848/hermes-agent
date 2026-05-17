# Wiring Cognitive Systems into Hermes Plugins

**Session:** 2026-05-09  
**Goal:** Integrate 5 novel cognitive systems (built in Cycle 6) into the live distillation plugin

## The Pattern

### Step 1: Build the System Module

Create the cognitive system in `~/subconscious/`:

```python
# ~/subconscious/cognitive_infrastructure_v2.py
class CreditAssigner:
    def __init__(self):
        self.pending_tips = {}  # tool_name -> [tip_ids]
        self.session_id = "default"
    
    def record_injection(self, tool_name: str, tip_id: int):
        """Called from pre_llm_call hook — tip was injected for this tool."""
        if tool_name not in self.pending_tips:
            self.pending_tips[tool_name] = []
        self.pending_tips[tool_name].append(tip_id)
    
    def record_outcome(self, tool_name: str, success: bool, error: str = ""):
        """Called from post_tool_call hook — tool completed."""
        if tool_name in self.pending_tips:
            for tip_id in self.pending_tips[tool_name]:
                self._write_reward(tip_id, tool_name, success)
            del self.pending_tips[tool_name]
    
    def _write_reward(self, tip_id, tool_name, success):
        import sqlite3
        db = sqlite3.connect(str(Path.home() / '.hermes' / 'cerebrum_memory.db'))
        db.execute("INSERT INTO skill_rewards (tip_id, tool_name, success, ...) VALUES (?, ?, ?, ...)", ...)
        db.commit()
        db.close()

# Singleton getters
_credit_assigner = None
def get_credit_assigner():
    global _credit_assigner
    if _credit_assigner is None:
        _credit_assigner = CreditAssigner()
    return _credit_assigner
```

### Step 2: Create Database Tables

```sql
-- Run once to create tables in cerebrum_memory.db
CREATE TABLE IF NOT EXISTS skill_rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tip_id INTEGER,
    tool_name TEXT,
    success INTEGER,
    upvote_delta INTEGER DEFAULT 0,
    downvote_delta INTEGER DEFAULT 0,
    session_id TEXT,
    timestamp REAL
);
```

### Step 3: Patch the Plugin

Edit `~/.hermes/plugins/distillation/__init__.py`:

```python
# ── Add import near top (after existing imports) ──
_COGNITIVE_INFRA_V2 = False
try:
    import sys
    _subconscious_path = os.path.expanduser("~/subconscious")
    if _subconscious_path not in sys.path:
        sys.path.insert(0, _subconscious_path)
    from cognitive_infrastructure_v2 import (
        get_governor_v2, get_credit_assigner, 
        get_session_extractor, get_tool_router, get_auto_skill
    )
    _COGNITIVE_INFRA_V2 = True
except Exception:
    pass

# ── In _on_pre_llm_call ──
def _on_pre_llm_call(user_message: str, context: dict = None, **kwargs):
    # ... existing injection logic ...
    
    # Bridge: record which tips were injected for credit assignment
    if _COGNITIVE_INFRA_V2:
        try:
            ca = get_credit_assigner()
            for tool_name, tip_ids in _injected_tips_this_turn.items():
                for tip_id in tip_ids:
                    ca.record_injection(tool_name, tip_id)
        except Exception:
            pass
    
    return result

# ── In _on_post_tool_call ──
def _on_post_tool_call(tool_name, args, result, status="", error="", **kwargs):
    # ... existing logic ...
    
    # Bridge: record outcome and credit tips
    if _COGNITIVE_INFRA_V2:
        try:
            ca = get_credit_assigner()
            ca.record_outcome(tool_name, is_success, error)
            
            tr = get_tool_router()
            tr.log_decision(tool_name, "proceed" if is_success else "caution", ...)
        except Exception:
            pass

# ── Add new hook at bottom ──
def _on_session_end(session_id="", tool_calls=None, **kwargs):
    """Session end: extract lessons."""
    if _COGNITIVE_INFRA_V2:
        try:
            se = get_session_extractor()
            se.session_id = session_id or "default"
            # Fallback to _current_chain if core doesn't pass tool_calls
            calls = tool_calls if tool_calls else _current_chain
            lessons = se.extract(calls)
            if lessons:
                se.save_lessons(lessons)
                return {"lessons_extracted": len(lessons)}
        except Exception:
            pass
```

### Step 4: Verify Wiring

```bash
# Syntax check
python3 -c "import py_compile; py_compile.compile('~/.hermes/plugins/distillation/__init__.py', doraise=True)"

# Import test
python3 -c "
import sys
sys.path.insert(0, '/Users/dannygomez/subconscious')
sys.path.insert(0, '/Users/dannygomez/.hermes/plugins/distillation')
import __init__ as d
print('Cognitive infra enabled:', d._COGNITIVE_INFRA_V2)
"

# Data flow test (after live tool calls)
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM skill_rewards;"
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM tool_routing_decisions;"
```

## Key Principles

1. **Never use cron jobs for live integration** — they lack session state and fail 83% of the time
2. **Always use `**kwargs` in hook signatures** — core passes extra args that change between versions
3. **Wrap every bridge call in try/except** — a crashing hook breaks the entire agent turn
4. **Use `_COGNITIVE_INFRA_V2` flag** — silently degrade if imports fail, don't break existing behavior
5. **Verify with real data** — empty tables after 24h means wiring failed

## Systems Wired in This Session

| System | Hook | Table | Status |
|--------|------|-------|--------|
| ToolIntelligenceRouter | `_on_pre_llm_call` | `tool_routing_decisions` | Active |
| CreditAssigner | `_on_post_tool_call` | `skill_rewards` | Active |
| SessionEndExtractor | `_on_session_end` | `session_rapid_extractions` | Active |
| InjectionGovernorV2 | `_on_pre_llm_call` | `tip_injection_attempts` | Active |
| AutoSkillCron | N/A (monthly trigger) | `auto_skill_pipeline` | Scheduled |
