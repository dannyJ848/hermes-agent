# soma-visual-diff-detector

*Researched: 2026-04-05 02:17 CDT*

# SOMA Visual Diff Detector

## Location
`~/subconscious/soma_visual_diff.py`

## Purpose
Pixel-level screenshot comparison for SOMA's 3D anatomy viewer. Enables visual regression testing between builds.

## Features
- Baseline registration: First screenshot becomes the baseline for a label
- Pixel-level diffing: Compares every pixel between baseline and current
- Annotated diff output: Red overlay on changed regions, saved as PNG
- Threshold-based pass/fail: Configurable diff percentage threshold (default 10%)
- PIL fallback: Works without pixelmatch using ImageChops.difference

## Usage
```bash
# List registered baselines
python3 ~/subconscious/soma_visual_diff.py --list

# Register baseline (first run auto-creates baseline)
python3 ~/subconscious/soma_visual_diff.py --test "homepage" screenshot.png

# Compare two images directly
python3 ~/subconscious/soma_visual_diff.py --compare baseline.png current.png --threshold 0.05

# Run test against existing baseline
python3 ~/subconscious/soma_visual_diff.py --test "homepage" new_screenshot.png
```

## Integration Path
1. SOMA's Vite dev server on :1420 can be screenshotted via browser_vision
2. Before each code change, capture baseline of key views
3. After change, capture again and run diff
4. Fail CI if diff exceeds threshold on critical views

## Technical Notes
- pixelmatch Python port had pip install issues (InvalidVersion error on Anaconda Python 3.8)
- PIL fallback works well: ImageChops.difference + per-pixel threshold of 10 per channel
- Diff images saved to `~/.soma/visual_tests/` with timestamps
- Baselines stored in `~/.soma/visual_tests/baselines/`


## Sources

- https://pypi.org/project/pixelmatch/
- https://github.com/mapbox/pixelmatch
