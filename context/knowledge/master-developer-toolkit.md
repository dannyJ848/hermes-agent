# master-developer-toolkit

*Researched: 2026-04-02 00:00 CDT*

# Master Developer Toolkit: Reverse Engineering + Algorithm Design + Program Deconstruction

## REVERSE ENGINEERING TOOLS

| Tool | Type | Best For | Install |
|------|------|----------|---------|
| Ghidra (NSA) | Decompiler | Full static analysis, C output, free | `brew install --cask ghidra` |
| radare2 | CLI disassembler | Scriptable, fast, headless analysis | `brew install radare2` |
| Binary Ninja | Decompiler | Best output quality, commercial | binary.ninja ($149+) |
| Frida | Dynamic instrumentation | Hook live functions, trace calls | `pip install frida-tools` |
| x64dbg | Debugger | Windows native debugging | Windows only |
| IDA Pro | Disassembler | Industry standard, expensive | hex-rays.com ($1000+) |
| capstone | Disassembly framework | Embeddable, Python bindings | `pip install capstone` |
| angr | Binary analysis | Symbolic execution, automatic | `pip install angr` |
| Cutter | GUI for radare2 | Visual RE workflow | `brew install --cask cutter` |

## APP DECOMPILATION BY TYPE

### Electron Apps
1. `cd /Applications/App.app/Contents/Resources`
2. `asar extract app.asar extracted/`
3. Read the JavaScript directly -- it's uncompiled
4. Webpack bundles: `grep -r "webpackJsonp" extracted/`
5. Source maps: check for `.js.map` files

### Tauri Apps
1. Frontend HTML/CSS/JS in Resources (sometimes accessible)
2. Rust backend compiled to native -- use Ghidra/radare2
3. `find App.app -name "*.js" -o -name "*.html"`

### Web Apps (React/Vue)
1. Browser DevTools -> Sources
2. Source maps: `curl site.com/main.js.map | npx shuji`
3. Webpack bundle analysis with grep for module IDs

### Native Binaries
1. `file binary` to detect format
2. `strings binary | grep "::"` for Rust crate paths
3. `r2 -A binary` then `afl` (functions), `ii` (imports), `pdg @ main` (decompile)

## ALGORITHM ANALYSIS FRAMEWORK

### Spaced Repetition (Anki) -- SM-2
- State: ease_factor (>= 1.3), interval (days), repetitions (count)
- After correct (quality >= 3): interval = 1, 6, then interval * ease_factor
- After incorrect: reset to interval=1, repetitions=0
- Ease update: EF' = EF + (0.1 - (5-q)*(0.08 + (5-q)*0.02))

### FSRS (Anki's new algorithm)
- Three-component memory model: DSR
  - D (Difficulty): inherent complexity of info
  - S (Stability): days for R to drop from 100% to 90%
  - R (Retrievability): current recall probability
- R = (1 + elapsed/(9*S))^-1
- ML-optimized parameters from review history
- Superior to SM-2: fewer reviews for same retention

### Algorithm Design Patterns to Master
1. **Memoization/DP**: Optimal substructure + overlapping subproblems
2. **Graph traversal**: BFS/DFS, Dijkstra, A*, topological sort
3. **Divide and conquer**: Merge sort, FFT, Strassen
4. **Greedy**: Activity selection, Huffman, Kruskal
5. **Sliding window**: Substring problems, streaming data
6. **Two pointers**: Array pair problems, palindromes
7. **Backtracking**: Constraint satisfaction, combinatorics
8. **Segment trees**: Range queries, lazy propagation
9. **Trie**: Prefix matching, autocomplete
10. **Union-Find**: Connected components, Kruskal's

## PROGRAM DECONSTRUCTION METHODOLOGY

### For ANY program:
1. **IDENTIFY**: Language, framework, architecture type
2. **UNPACK**: Extract source/assets/bundles
3. **MAP**: Dependency graph, entry points, data flow
4. **TRACE**: Follow main execution paths
5. **EXTRACT**: Core algorithms and data structures
6. **DOCUMENT**: Architecture diagram, component relationships
7. **REBUILD**: Recreate key components from understanding
8. **IMPROVE**: Apply learned patterns to enhance

### Tools for each step:
- Identify: `file`, `strings`, `head`, `cat package.json`
- Unpack: `asar`, `unzip`, Ghidra import
- Map: `grep -r "import\|require\|from"`, dependency-cruiser
- Trace: Frida hooks, `console.log` injection, debugger
- Extract: Read decompiled output, identify patterns
- Document: Mermaid/Excalidraw diagrams
- Rebuild: Implement in clean Python/TypeScript
- Improve: Benchmark, optimize, extend

## SELF-ADAPTIVE GROWTH ALGORITHM (SAGA)
See skill: self-adaptive-growth-algorithm
- FSRS-based retention for all learned skills
- GEPA-style evolution from execution traces
- Phantom-style 5-gate validation
- Exponential compounding via adjacency graph


## Sources

- https://appsecsanta.com/mobile-security-tools/radare2-vs-ghidra
- https://www.todesktop.com/blog/posts/how-to-decompile-a-production-electron-app-on-mac
- https://faqs.ankiweb.net/what-spaced-repetition-algorithm
- https://news.ycombinator.com/item?id=42908863
- https://gist.github.com/0xdevalias/8c621c5d09d780b1d321bfdb86d67cdd
