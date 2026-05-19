---
name: reverse-engineering-master
version: 1.0
created: 2026-04-02
description: Reverse engineer any application -- decompile, analyze algorithms, reconstruct. Covers Electron, Tauri, web, native binaries. Extract and understand any program's construction.
tags: [reverse-engineering, decompilation, binary-analysis, ghidra, algorithms]
---

# Reverse Engineering Master

## Tool Arsenal

### 1. Ghidra (NSA, Free, Java-based)
```bash
# Install
brew install --cask ghidra

# Headless analysis (no GUI needed)
analyzeHeadless /tmp/project proj_name -import target_binary -scriptPath /tmp/scripts -postScript analyze.py

# Key features: decompilation to C, control flow graphs, type inference
```

### 2. radare2 (CLI-first, scriptable)
```bash
brew install radare2

# Quick binary analysis
r2 -A target_binary        # Auto-analyze
aaa                         # Analyze all
afl                         # List functions
pdf @ main                  # Disassemble main
VV                          # Visual mode (ASCII graph)

# Script via r2pipe
pip install r2pipe
```

```python
import r2pipe
r2 = r2pipe.open("target_binary")
r2.cmd("aaa")                    # Analyze all
functions = r2.cmd("afl")        # List all functions
main_decompiled = r2.cmd("pdg @ main")  # Decompile main (if r2ghidra installed)
```

### 3. Binary Ninja (Commercial, best decompiler)
- Best-in-class decompilation output
- Python API for automation
- URL: https://binary.ninja/

### 4. Frida (Dynamic instrumentation)
```bash
pip install frida-tools

# Attach to running process and trace calls
frida-trace -p PID -i "*algorithm*"

# Inject JavaScript to hook functions
frida -p PID -l hook.js
```

## Application Type Detection & Unpacking

### Electron Apps
```bash
# 1. Locate app
cd /Applications/TargetApp.app/Contents/Resources

# 2. Extract ASAR archive
npm install -g asar
asar extract app.asar extracted/

# 3. Read source (it's JavaScript!)
cat extracted/src/main.js
cat extracted/package.json  # dependencies, entry point

# 4. Analyze webpack bundles
# Find: webpackJsonp, chunk IDs, module map
grep -r "webpackJsonp" extracted/
grep -r "chunkId" extracted/
```

### Tauri Apps (like SOMA)
```bash
# 1. Tauri bundles HTML/CSS/JS in the binary's resource section
# macOS: inside .app/Contents/Resources/
# The frontend is usually accessible directly

# 2. For the compiled Rust backend:
# Use Ghidra or radare2 on the binary
r2 -A /Applications/TargetApp.app/Contents/MacOS/TargetApp

# 3. The JS/TS frontend can often be found:
find /Applications/TargetApp.app -name "*.js" -o -name "*.html"
```

### Web Apps (React/Vue/Angular)
```bash
# 1. Browser DevTools -> Sources tab
# 2. Look for webpack:// in source tree
# 3. Use source maps if available:
curl https://target.app/static/js/main.js.map -o main.js.map
npx shuji main.js.map -o recovered_src/

# 4. Webpack bundle analysis
npm install -g webpack-bundle-analyzer
# Point at the bundle, get dependency tree
```

### Native Binaries (C/C++/Rust/Go)
```bash
# Detect language/compiler
file target_binary
strings target_binary | grep -i "rust\|cargo\|go build\|gcc"

# Go binaries: recover source structure
# Install GoReSym
go install github.com/mandiant/GoReSym@latest
GoReSym -t -d -p target_binary

# Rust binaries: look for panic strings, crate names
strings target_binary | grep "::" | head -30

# Full disassembly workflow
r2 -A target_binary
> afl          # list all functions  
> ii           # imports (what libraries it uses)
> iE           # exports (what it exposes)
> pdg @ main   # decompile main
```

## Algorithm Extraction Pattern

For any algorithm (e.g., Anki's SM-2, Spotify's recommendation):

### Step 1: Locate the algorithm
```bash
# Search for keywords in decompiled/disassembled code
r2> / algorithm
r2> / schedule  
r2> / interval
r2> / repeat

# In JavaScript bundles:
grep -r "interval\|repetition\|ease\|factor" extracted/
```

### Step 2: Extract pseudocode
From Ghidra/radare2 decompilation, or from JavaScript source directly.

### Step 3: Implement in Python
```python
# Example: Anki SM-2 Algorithm (simplified)
def sm2(quality, ease_factor, interval, repetitions):
    """
    quality: 0-5 (0=complete failure, 5=perfect)
    ease_factor: >= 1.3
    interval: current interval in days
    repetitions: number of consecutive correct answers
    """
    if quality >= 3:  # Correct response
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetitions += 1
    else:  # Incorrect response
        repetitions = 0
        interval = 1
    
    # Update ease factor
    ease_factor = max(1.3, ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    
    return interval, ease_factor, repetitions
```

### Step 4: Build test harness
```python
import pytest

def test_sm2_first_correct():
    interval, ef, reps = sm2(4, 2.5, 0, 0)
    assert interval == 1  # First review: 1 day
    assert reps == 1

def test_sm2_second_correct():
    interval, ef, reps = sm2(4, 2.5, 1, 1)
    assert interval == 6  # Second: 6 days

def test_sm2_fifth_correct():
    interval, ef, reps = sm2(4, 2.5, 6, 2)
    assert interval == 15  # 6 * 2.5 = 15
```

### Step 5: Enhance
- Identify weaknesses in original algorithm
- Apply improvements (e.g., FSRS improves on SM-2 by modeling DSR memory state)
- Benchmark original vs enhanced

## File Format Analysis

### Any binary format:
```python
import struct

def analyze_binary_format(filepath):
    """Read magic bytes and identify file format."""
    with open(filepath, 'rb') as f:
        header = f.read(32)
    
    magic_map = {
        b'\x89PNG': 'PNG image',
        b'PK\x03\x04': 'ZIP/JAR/APK/DOCX',
        b'\x1f\x8b': 'GZIP',
        b'%PDF': 'PDF',
        b'\x7fELF': 'Linux ELF binary',
        b'\xfe\xed\xfa\xce': 'macOS Mach-O 32-bit',
        b'\xfe\xed\xfa\xcf': 'macOS Mach-O 64-bit',
        b'\xcf\xfa\xed\xfe': 'macOS Mach-O 64-bit (rev)',
        b'MZ': 'Windows PE executable',
        b'DICM': 'DICOM medical image',
        b'II*\x00': 'TIFF (little-endian)',
        b'MM\x00*': 'TIFF (big-endian)',
    }
    
    for magic, fmt in magic_map.items():
        if header.startswith(magic):
            return fmt
    
    return f"Unknown (header: {header[:8].hex()})"
```

## Pitfalls
- Always respect copyright and licensing when analyzing others' software
- Ghidra requires Java 17+ -- install with `brew install openjdk@17`
- radare2's decompiler (r2ghidra) needs separate plugin install
- Electron apps with bytenode compile JS to V8 bytecode -- harder but still reversible
- Tauri Rust code is compiled to native -- requires real RE skills, not just reading JS
- Webpack source maps are the goldmine -- always check for .js.map files first
