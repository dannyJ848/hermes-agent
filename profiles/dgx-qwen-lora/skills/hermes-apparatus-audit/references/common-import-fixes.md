# Common Import Fixes During Audits

**Pattern:** Modules in `agent/` sometimes use bare imports like `from cognitive_infrastructure_v2 import ...` instead of the proper `from agent.cognitive_infrastructure_v2 import ...`. This breaks when the module is imported as part of the `agent.` package namespace.

**Detection:**
```
✗ IMPORT ERRORS (1):
  cognitive_infrastructure_hooks: No module named 'cognitive_infrastructure_v2'
```

**Fix:**
```python
# WRONG (line 20 of cognitive_infrastructure_hooks.py)
from cognitive_infrastructure_v2 import (
    get_governor_v2, get_credit_assigner, get_session_extractor,
    get_tool_router, get_auto_skill
)

# CORRECT
from agent.cognitive_infrastructure_v2 import (
    get_governor_v2, get_credit_assigner, get_session_extractor,
    get_tool_router, get_auto_skill
)
```

**Why it happens:** When a module is run standalone or imported via a different path, bare imports can work. But when loaded through the `agent.` package namespace (as Hermes does), Python needs the full dotted path.

**Prevention:** Always use `from agent.X import ...` for imports within the `agent/` directory.

**Date:** May 10, 2026
**File fixed:** `/Users/dannygomez/hermes-agent/agent/cognitive_infrastructure_hooks.py` line 20
