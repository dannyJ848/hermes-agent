# Class Name Mismatch Recovery

## Scenario

The `context_compressor.py` file was replaced with a new `AdaptiveCompressor` class (104 lines), but `run_agent.py` still expected the old `ContextCompressor` class (1661 lines) with its full constructor signature. The import alias `from agent.context_compressor import AdaptiveCompressor as ContextCompressor` only fixed the `ImportError` but broke at instantiation time because the constructor signatures were completely different.

## Detection

Error pattern:
```
TypeError: AdaptiveCompressor.__init__() got an unexpected keyword argument 'model'
```

This happens at `run_agent.py` line where `ContextCompressor(model=self.model, threshold_percent=..., ...)` is called.

## Root Cause

1. File was overwritten with a new class that has a different constructor
2. The old class had many methods that the new one doesn't have
3. The import alias made the import succeed but the instantiation fail

## Recovery Procedure

### Step 1: Retrieve original from git
```bash
cd ~/hermes-agent
git show <commit>:agent/context_compressor.py > /tmp/context_compressor_original.py
```

### Step 2: Combine both classes in one file
Use a Python script to prepend the original class and append the new one with a clear separator:

```python
from pathlib import Path

original = Path("/tmp/context_compressor_original.py").read_text()
current = Path("~/hermes-agent/agent/context_compressor.py").read_text()

# Prepend original, append new with separator
combined = original + "\n\n" + "#" * 80 + "\n# NEW CLASS — Added alongside original\n" + "#" * 80 + "\n\n" + current

Path("~/hermes-agent/agent/context_compressor.py").write_text(combined)
```

### Step 3: Revert the import alias
Change:
```python
from agent.context_compressor import AdaptiveCompressor as ContextCompressor
```
Back to:
```python
from agent.context_compressor import ContextCompressor
```

### Step 4: Verify all methods exist
```python
import re
content = Path("~/hermes-agent/run_agent.py").read_text()
methods = re.findall(r'self\.context_compressor\.(\w+)', content)
for m in sorted(set(methods)):
    print(f"  {m}")
```

Ensure each method exists in the restored `ContextCompressor` class.

## Prevention

1. **Never overwrite a core class file** without checking who imports it
2. **Always grep for `from agent.X import`** before modifying `agent/X.py`
3. **If adding a new class alongside an old one**, append it with a clear namespace, don't replace
4. **Test instantiation** not just import: `python -c "from agent.X import Y; y = Y(...)"`
