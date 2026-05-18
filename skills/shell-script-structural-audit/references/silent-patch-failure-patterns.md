# Silent Patch Failure Patterns

## Problem
`str.replace()` and `patch` return "success" even when the replacement string
doesn't match -- the count just stays 0. This creates false confidence.

## Detection Methods
1. **Count before AND after**: Track `content.count('target')` before and after
   replacement. If both are 0, the patch didn't match AND didn't create.
2. **Line-number verification**: After patching, `grep -n 'target'` and confirm
   the target appears on the expected line number.
3. **Read the actual lines**: `read_file(offset=N, limit=5)` at the exact line
   where the change should appear. Don't trust grep counts alone.

## Common Causes
- **Whitespace mismatch**: 4-space vs 8-space indent in heredocs
- **Escape differences**: `\\\"` in Python string vs `\"` in actual file
- **Line continuation differences**: `\\ \n` vs `\\n`
- **Duplicate blocks**: `replace(old, new, 1)` finds the FIRST match, not the
  one you intended -- or `replace_all=True` was needed
- **Unicode/invisible chars**: Non-breaking spaces, tab vs space mixing

## Reliable Patch Strategy
1. Use `read_file()` to get the EXACT text at the target location
2. Copy the exact text (including whitespace) as `old_string`
3. For line insertions, prefer `lines.insert(i, new_line)` over string replace
4. After ANY patch, immediately `read_file()` the changed area to verify
5. For multiple similar blocks, patch by line number not by string match