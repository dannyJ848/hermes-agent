# Autobrowse Pipeline Smoke Test — Verified Recipe

## Purpose
End-to-end verification that all 4 autobrowse modules are functional and wired correctly, independent of the Hermes core hook gap.

## When to Run
- After any autobrowse code changes
- After distillation plugin updates
- After Hermes version updates that might affect plugin loading
- When user asks "check autobrowse" or "smoke test the pipeline"

## Full Test Script

```python
from autobrowse_tracer import AutobrowseTracer
from autobrowse_analyzer import AutobrowseAnalyzer
from autobrowse_synthesizer import AutobrowseSynthesizer
from autobrowse_graduator import AutobrowseGraduator

t = AutobrowseTracer(session_id='smoke_test')
t.set_task_context('live smoke check')

# Pattern 1: Redundant loop — 3+ identical calls
for i in range(3):
    t.record_call(
        tool_name='web_search',
        model_used='kimi-for-coding',
        input_data={'query': 'same query'},
        output_data={'results': i+1},
        execution_time_ms=100,
        status='success',
        input_tokens=10,
        output_tokens=20
    )

# Pattern 2: Suboptimal model — expensive model for simple tool
t.record_call(
    tool_name='read_file',
    model_used='deepseek-v4-pro',
    input_data={'path': '/tmp/test'},
    output_data={'content': 'hello'},
    execution_time_ms=50,
    status='success',
    input_tokens=5,
    output_tokens=10
)

# Pattern 3: Failure cluster
t.record_call(
    tool_name='delegate_task',
    model_used='kimi-for-coding',
    input_data={'goal': 'fail'},
    output_data={'error': 'timeout'},
    execution_time_ms=2000,
    status='error',
    error_type='timeout',
    error_message='Timed out',
    input_tokens=50,
    output_tokens=0
)

# Analyze
a = AutobrowseAnalyzer()
patterns = a.analyze_traces(t.traces)
assert len(patterns) >= 2, f"Expected 2+ patterns, got {len(patterns)}"

# Synthesize
s = AutobrowseSynthesizer()
tips = s.generate_tips(patterns)
assert len(tips) >= 1, f"Expected 1+ tips, got {len(tips)}"
for tip in tips:
    assert 'condition' in tip, "Tip missing 'condition' key"
    assert 'recommendation' in tip, "Tip missing 'recommendation' key"
    assert 'domain' in tip, "Tip missing 'domain' key"

# Grade
if tips:
    g = AutobrowseGraduator()
    for tip in tips:
        tip_id = tip['condition'][:40]
        g.record_application(tip_id, success=True)
    report = g.get_lifecycle_report()
    assert report['total_tracked'] >= 1, "Expected tracked tips"

# Strategy.md updated
assert s.strategy_path.exists(), "strategy.md not created"
assert s.strategy_path.stat().st_size > 0, "strategy.md is empty"

print("=== FULL PIPELINE: PASS ===")
```

## Expected Results

| Stage | Expected | Notes |
|-------|----------|-------|
| Traces recorded | 5 | 3 redundant + 1 suboptimal + 1 failure |
| Patterns detected | 2+ | redundant_loop + suboptimal_model minimum |
| Tips generated | 1+ | WHEN/DO format dicts |
| Tips persisted | 0+ | Duplicate key errors are NORMAL — means dedup works |
| Strategy.md | Updated | File size should grow |
| Lifecycle report | 1+ tracked | Graduator tracks applications |

## Common Gotchas

**Duplicate key errors from CortexDB.insert_node**: These are EXPECTED and HARMLESS. The `cortex_active_tip_md5_uniq` constraint prevents duplicate tips. If you see these, the deduplication system is working correctly.

**Method names differ from intuitive names**:
- `record_call()` not `record_tool_call()`
- `analyze_traces()` not `analyze_recent_traces()`
- `generate_tips()` not `synthesize_from_patterns()`
- `record_application(tip_id, success)` not `evaluate_tip(tip)`

**Analyzer needs 3+ identical calls** to trigger `redundant_loop`. Two calls is not enough.

**Suboptimal model detection** requires `deepseek-v4-pro` (rank 4) or `claude-opus` (rank 5) on a SIMPLE_TOOL like `read_file`, `web_search`, etc. Using `kimi-for-coding` won't trigger it because it's not in the cost rank map.

## Quick One-Liner Check

```bash
cd ~/subconscious && python3 -c "
from autobrowse_tracer import AutobrowseTracer
from autobrowse_analyzer import AutobrowseAnalyzer
from autobrowse_synthesizer import AutobrowseSynthesizer
t = AutobrowseTracer('test'); t.set_task_context('test')
for i in range(3): t.record_call('web_search', 'kimi-for-coding', {'q':'x'}, {'r':i}, 100, 'success', 10, 20)
a = AutobrowseAnalyzer(); p = a.analyze_traces(t.traces)
s = AutobrowseSynthesizer(); tips = s.generate_tips(p)
print(f'patterns={len(p)} tips={len(tips)}')
"
```

## Files
- `~/subconscious/autobrowse_tracer.py`
- `~/subconscious/autobrowse_analyzer.py`
- `~/subconscious/autobrowse_synthesizer.py`
- `~/subconscious/autobrowse_graduator.py`
- `~/subconscious/strategy.md`
