# Orphan Alias Cleanup

## Problem

Hermes profile aliases are shell wrapper scripts (e.g., `~/.local/bin/soma-coder`) that invoke `hermes -p <profile>`. When a profile is deleted or renamed, the wrapper script becomes an "orphan" — it points to a non-existent profile. `hermes doctor` detects these and warns:

```
⚠ Orphan alias: soma-coder → profile 'soma-coder' no longer exists
```

## Detection

The doctor checks `~/.local/bin/` (or the wrapper directory returned by `_get_wrapper_dir()`) for scripts containing `hermes -p <profile>` where the profile no longer exists.

To find orphans manually:

```bash
# List all wrapper scripts
ls ~/.local/bin/

# Check which profiles they point to
for f in ~/.local/bin/*; do
    if grep -q "hermes -p" "$f" 2>/dev/null; then
        profile=$(grep -oP 'hermes -p \K\S+' "$f")
        if ! hermes profile list | grep -q "$profile"; then
            echo "ORPHAN: $f → $profile"
        fi
    fi
done
```

## Cleanup

Simply remove the orphan wrapper scripts:

```bash
rm ~/.local/bin/soma-coder ~/.local/bin/soma-tester ~/.local/bin/soma-researcher
```

**Do NOT use `hermes profile alias --remove <name>`** — this fails with `Error: Profile 'X' does not exist` because the profile is already gone. The alias wrapper is just a stale file.

## Prevention

When deleting a profile, always clean up its alias:

```bash
# 1. Remove the alias wrapper FIRST (while profile still exists)
hermes profile alias --remove my-profile

# 2. Then delete the profile
hermes profile delete my-profile
```

If you delete the profile first, you'll need to manually `rm` the wrapper.

## Session Reference

- Date: 2026-05-17
- Orphans found: `soma-coder`, `soma-tester`, `soma-researcher`
- Location: `~/.local/bin/`
- Fix: `rm ~/.local/bin/soma-*`
- Result: `hermes doctor` no longer reports orphan aliases
- Status: ✅ COMPLETED — aliases removed, doctor clean
