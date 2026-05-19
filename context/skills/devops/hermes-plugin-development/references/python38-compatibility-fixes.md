# Python 3.8 Compatibility Fixes for Hermes Agent

## Problem

Hermes Agent codebase uses Python 3.10+ union syntax (`X | None`) but the system Python may be 3.8.8. This causes:

```
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

## Affected Files

- `hermes_constants.py` — `get_optional_skills_dir(default: Path | None = None)`
- `hermes_constants.py` — `get_subprocess_home() -> str | None`
- Any file with `-> Type | None:` or `: Type | None =` annotations

## Fix Pattern

### Single function fix

```python
# BEFORE (Python 3.10+):
def get_optional_skills_dir(default: Path | None = None) -> Path:

# AFTER (Python 3.8 compatible):
from typing import Optional  # Add at top of file

def get_optional_skills_dir(default=None):
    """Return the optional-skills directory."""
    env_override = os.getenv("HERMES_OPTIONAL_SKILLS")
    if env_override:
        return Path(env_override)
    if default is not None:
        return default
    return get_hermes_home() / "optional-skills"
```

### Bulk fix script

```python
import re

def fix_python38_annotations(filepath):
    """Fix union syntax annotations for Python 3.8 compatibility."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add Optional import if not present
    if 'from typing import' in content and 'Optional' not in content:
        content = content.replace(
            'from typing import',
            'from typing import Optional,'
        )
    elif 'from typing import' not in content:
        content = 'from typing import Optional\n' + content
    
    # Fix return type annotations: ) -> X | None:
    content = re.sub(
        r'\) -> ([A-Za-z_][A-Za-z0-9_\[\]]*) \| None:',
        r') -> Optional[\1]:',
        content
    )
    
    # Fix parameter type annotations: param: X | None =
    content = re.sub(
        r': ([A-Za-z_][A-Za-z0-9_\[\]]*) \| None =',
        r': Optional[\1] =',
        content
    )
    
    # Fix Path | None specifically
    content = content.replace(': Path | None =', ': Optional[Path] =')
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

# Usage
fix_python38_annotations('/Users/dannygomez/hermes-agent/hermes_constants.py')
```

## Prevention

**Always use venv Python:**
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 --version
```

The venv should have Python 3.10+ which supports union syntax natively.

## Files Known to Need Fixes

| File | Line | Problem |
|------|------|---------|
| `hermes_constants.py` | 110 | `get_optional_skills_dir(default: Path \| None = None) -> Path` |
| `hermes_constants.py` | 165 | `get_subprocess_home() -> str \| None` |
| `hermes_constants.py` | 124 | `get_hermes_dir(new_subpath: str, old_name: str) -> Path` |

## Verification

After fix:
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from hermes_cli.plugins import PluginManager
pm = PluginManager()
print('Plugin system loads OK')
"
```
