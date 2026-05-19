# Rebuilding YantrikDB Rust Extension for a New Python Version

## Problem

YantrikDB ships a Rust extension (`_yantrikdb_rust.cpython-XX-darwin.so`) compiled for a specific Python version. When Hermes runs in a venv with a different Python (e.g., 3.11 vs 3.8), the import fails:

```
ModuleNotFoundError: No module named 'yantrikdb._yantrikdb_rust'
```

The `_load_yantrikdb()` lazy import only works if the `.so` ABI is compatible. When it's not, the only fix is to rebuild.

## Prerequisites

- Rust toolchain (`cargo` available)
- `maturin` Python package
- YantrikDB source code at `~/.hermes/plugins/yantrikdb/`

## Rebuild Steps

### 1. Install maturin in the target venv

```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -m pip install maturin
```

### 2. Build the wheel for the target Python

```bash
cd ~/.hermes/plugins/yantrikdb
/Users/dannygomez/hermes-agent/venv/bin/python3 -m maturin build \
    --release \
    --interpreter /Users/dannygomez/hermes-agent/venv/bin/python3
```

Output: `target/wheels/yantrikdb-0.7.15-cp311-cp311-macosx_11_0_arm64.whl`

### 3. Install the wheel

```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -m pip install \
    target/wheels/yantrikdb-*.whl --force-reinstall
```

This reinstalls `yantrikdb`, `click`, and `uuid-utils`.

### 4. Verify

```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -c "
from yantrikdb import YantrikDB
db = YantrikDB.with_default('/tmp/test_ydb.db')
result = db.recall('test', top_k=1)
print(f'Import OK, recall returned {len(result)} results')
db.close()
"
```

### 5. Verify through Hermes plugin path

```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -c "
from plugins.memory import discover_memory_providers, load_memory_provider
providers = discover_memory_providers()
for name, desc, avail in providers:
    print(f'{name}: available={avail}')
provider = load_memory_provider('yantrikdb')
print(f'Loaded: {provider.name}, available={provider.is_available()}')
"
```

## Common Issues

### pip version parsing error during maturin install

If `maturin develop` fails with:
```
pip._vendor.packaging.version.InvalidVersion: Invalid version: '4.0.0-unsupported'
```

Use `maturin build` instead of `maturin develop`. The `develop` command calls pip install which can choke on system packages with weird version strings.

### pyzmq version warning

```
WARNING: Error parsing dependencies of pyzmq: Invalid version: 'cpython'
```

This is harmless — the wheel still builds successfully.

## When NOT to rebuild

- If the `.so` happens to be ABI-compatible (rare across major Python versions)
- If you can switch Hermes to run on the Python version the `.so` was built for
- If you're using a pure-Python fallback (not recommended for production)

## Session Reference

- Date: 2026-05-17
- Venv Python: 3.11.14
- System Python with working YantrikDB: 3.8.8 (anaconda)
- Fix: Built `yantrikdb-0.7.15-cp311-cp311-macosx_11_0_arm64.whl`
- Result: `yantrikdb` provider `is_available()` changed from `False` to `True`
- Status: ✅ COMPLETED — Rust extension rebuilt, plugin loads successfully
