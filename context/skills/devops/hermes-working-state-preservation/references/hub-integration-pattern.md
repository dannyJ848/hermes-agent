# Hub Integration Pattern — Bulk Skill/Plugin Ingestion

## Date: 2026-05-16

## Problem

User discovers multiple community repos (HermesHub, Superpowers, Obsidian skills, etc.) and wants them downloaded, built, and integrated into their Hermes Agent setup in one shot. This involves:
- Cloning multiple repos
- Identifying skill vs plugin vs tool content
- Building TypeScript/Rust projects
- Handling Python version mismatches
- Avoiding name collisions in `~/.hermes/skills/`
- Reporting what worked and what didn't

## Protocol

### 1. Clone All Repos First

```bash
mkdir -p ~/hermes-hub-repos
cd ~/hermes-hub-repos
git clone --depth 1 <repo-url-1>
git clone --depth 1 <repo-url-2>
# ... etc
```

Use `--depth 1` — these are throwaway clones for extraction, not development.

### 2. Inspect Structure Before Copying

Each repo may organize differently:

| Repo Type | Typical Layout | Action |
|-----------|---------------|--------|
| HermesHub-style | `skills/<name>/SKILL.md` | Copy `skills/*` directly to `~/.hermes/skills/` |
| Superpowers-style | `skills/<name>/SKILL.md` | Prefix with `superpowers-` to avoid collisions |
| Obsidian-style | `skills/<name>/SKILL.md` | Prefix with `obsidian-` |
| TypeScript plugin | `src/`, `package.json`, `dist/` | `npm install && npm run build`, copy to `~/.hermes/plugins/` |
| Rust+Python | `Cargo.toml`, `pyproject.toml`, `src/` | Patch Python version if needed, `pip install -e .`, copy to `~/.hermes/plugins/` |

### 3. Handle Name Collisions

Before copying, check if destination exists:

```python
import os, shutil

def install_skill(src_dir, dst_dir, prefix=""):
    name = os.path.basename(src_dir)
    if prefix:
        name = f"{prefix}-{name}"
    dst = os.path.join(os.path.expanduser("~/.hermes/skills"), name)
    if os.path.exists(dst):
        return f"⚠️  {name} already exists, skipping"
    shutil.copytree(src_dir, dst)
    return f"✅ {name}"
```

### 4. Build TypeScript Projects

```bash
cd <plugin-dir>
npm install
npm run build
# Verify dist/ exists
ls dist/
```

If build succeeds, copy entire repo to `~/.hermes/plugins/<name>/`.

### 5. Handle Python Version Mismatches (YantrikDB Pattern)

When `pyproject.toml` requires Python >=3.10 but system has 3.8:

```bash
# 1. Patch version requirement
sed -i '' 's/requires-python = ">=3.10"/requires-python = ">=3.8"/' pyproject.toml

# 2. Install editable
python3 -m pip install -e .

# 3. If Rust extension fails (arch mismatch), check Python-only fallback
python3 -c "import yantrikdb; print(yantrikdb.__version__)"
```

**Arch mismatch fix:**
```bash
# If Rust builds arm64 but Python is x86_64:
rustup target add x86_64-apple-darwin
CARGO_BUILD_TARGET=x86_64-apple-darwin python3 -m pip install -e . --force-reinstall
```

### 6. Report Summary

Always produce a summary with:
- Total skills installed by source
- Total plugins installed
- Build successes/failures
- Version/arch issues encountered
- File paths for everything

Save to `~/.hermes/memory/hub-integration-YYYY-MM-DD.md`.

## Pitfalls

- **Don't assume pip exists:** Use `python3 -m pip` not bare `pip`
- **Don't ignore arch mismatches:** Rust extensions built for wrong arch will fail at import time
- **Don't skip collision checks:** Overwriting existing skills destroys user customizations
- **Don't forget to build:** TypeScript skills need `npm run build` before they're usable
- **Don't leave repos in ~/hermes-hub-repos/:** These are throwaway — the installed copies in `~/.hermes/skills/` and `~/.hermes/plugins/` are what matter

## Example: Full Integration Command Sequence

```bash
# 1. Clone
mkdir -p ~/hermes-hub-repos && cd ~/hermes-hub-repos
git clone --depth 1 https://github.com/amanning3390/hermeshub.git
git clone --depth 1 https://github.com/obra/superpowers.git
git clone --depth 1 https://github.com/kepano/obsidian-skills.git
git clone --depth 1 https://github.com/NousResearch/hermes-paperclip-adapter.git
git clone --depth 1 https://github.com/yantrikos/yantrikdb.git

# 2. Copy skills (with prefixes)
cp -r hermeshub/skills/* ~/.hermes/skills/
for d in superpowers/skills/*; do cp -r "$d" ~/.hermes/skills/superpowers-$(basename "$d"); done
for d in obsidian-skills/skills/*; do cp -r "$d" ~/.hermes/skills/obsidian-$(basename "$d"); done

# 3. Build paperclip
cd hermes-paperclip-adapter && npm install && npm run build
cp -r . ~/.hermes/plugins/paperclip-adapter

# 4. Install yantrikdb
cd ../yantrikdb
sed -i '' 's/>=3.10/>=3.8/' pyproject.toml
python3 -m pip install -e .
cp -r . ~/.hermes/plugins/yantrikdb

# 5. Verify
echo "Skills: $(ls ~/.hermes/skills | wc -l)"
echo "Plugins: $(ls ~/.hermes/plugins | wc -l)"
```
