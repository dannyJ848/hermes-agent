# 3D anatomy label collision avoidance algorithms

*Researched: 2026-04-05 02:22 CDT*

# Label Collision Avoidance for 3D Anatomy Viewers

## Problem
When rendering anatomy labels in a 3D viewport (Three.js), labels overlap when multiple structures cluster together. As the camera rotates, projected 2D positions shift, causing dynamic overlaps.

## Research Sources & Key Findings

### 1. "Render or Nudge" Greedy Algorithm (O(n) — BEST FOR REAL-TIME)
**Source:** Wade Fagen-Ulmschneider, "Minimizing Overlapping Labels in Interactive Visualizations" (Towards Data Science, 2020)

- **Algorithm:** For each label in priority order: check if its bounding box overlaps any already-placed label. If no overlap → render at original position. If overlap → "nudge" up/down by label height until a free spot is found. If no spot → render at original (overlapping).
- **Complexity:** O(n) linear time — massively faster than force-directed.
- **Trade-off:** Doesn't guarantee zero overlaps but vastly improves readability.
- **Key insight:** Priority ordering matters — render important labels first (highlighted structures) so they get prime positions.
- **Perfect for SOMA because:** Real-time, runs every frame during camera rotation, O(n) is critical for 60fps on mobile.

### 2. Force-Directed Graph (D3 forceSimulation)
**Source:** D3.js force component; commonly used in chart labeling

- **Algorithm:** All labels have mutual repulsion forces. Run physics simulation until stable. Labels converge to non-overlapping positions.
- **Complexity:** O(n³) — far too slow for real-time 3D viewport with continuous camera rotation.
- **Verdict:** NOT suitable for SOMA's use case. Good for static charts, not interactive 3D.

### 3. Bitmap-Based Overlap Detection (FastLabels, UW 2021)
**Source:** "Fast and Flexible Overlap Detection for Chart Labeling with Bitmaps" — VIS 2021 (idl.cs.washington.edu)

- **Algorithm:** Maintain an occupancy bitmap (1-bit per pixel). When placing a label, rasterize its bounding box to bitmap and check for collisions in O(1). Place label if bitmap area is clear, mark pixels as occupied.
- **Complexity:** O(n) placement, O(1) per overlap check.
- **Advantage:** Extremely fast for many labels (hundreds+), GPU-friendly.
- **SOMA integration:** Could use a 2D canvas as occupancy grid, updated per frame.

### 4. Dynamic Non-Overlapping Label Placement for 3D Viewports (OSTI/DOE)
**Source:** "Dynamic non-overlapping label placement for three-dimensional..." — Technical report (osti.gov/servlets/purl/1142737)

- **Algorithm:** Screen-axis-aligned rectangular labels placed with constraint solving. Labels connected to 3D points via leader lines. Rasterizes viewport to check occupancy.
- **Key technique:** Labels placed at varying heights (z-layers) to prevent overlap. Rasterize the viewport each frame.
- **Relevant sections:** Problem Definition, Data Structures, Algorithm, Implementation.

### 5. Three.js CSS2DRenderer + Force Approach
**Source:** Three.js forum thread #37487

- **Challenge:** CSS2DRenderer positions elements absolutely in screen space. No built-in overlap avoidance.
- **Community consensus:** No easy way — must implement custom collision detection on the projected 2D positions.
- **Approach:** Project Vector3 → NDC → screen coords, then run collision avoidance on the 2D overlay.

## Recommended Algorithm for SOMA

**Hybrid: Priority "Render or Nudge" + Occupancy Bitmap**

```
1. Each frame (after camera change):
   a. Project all label anchor points (Vector3 → screen coords)
   b. Sort labels by priority (currently selected > visible > occluded)
   c. Clear occupancy bitmap
   d. For each label in priority order:
      - Calculate bounding box at projected position
      - Check occupancy bitmap for overlap
      - If clear → place label, mark bitmap
      - If overlap → nudge vertically (±labelHeight, up to 3 attempts)
      - If still overlapping → reduce opacity, place at original position
   e. Draw leader lines from label to anchor point
```

**Performance budget:** With 30-50 anatomy labels at 60fps on mobile, the bitmap approach with O(n) greedy placement should take <1ms per frame.

**Data structure:** A shared `label-avoidance.ts` module with:
- `projectToScreen(vector3, camera): {x, y}` — projects 3D to 2D
- `occupancyBitmap: Uint8Array` — 1-bit per 4px grid cell
- `placeLabel(label, bitmap): {x, y, opacity}` — greedy placement
- `drawLeaderLine(from, to): Path2D` — SVG/canvas connector

## Leader Lines
When nudged, labels need leader lines connecting them to the original anchor point. These should:
- Be thin (1px), semi-transparent
- Use a slight curve (quadratic bezier) for elegance
- Not overlap with other leader lines (lower priority — acceptable trade-off)


## Sources

- https://towardsdatascience.com/minimizing-overlapping-labels-in-interactive-visualizations-b0eabd62ef0/
- https://discourse.threejs.org/t/how-to-display-multiple-2d-labels-without-overlapping-them/37487
- https://www.osti.gov/servlets/purl/1142737
- https://idl.cs.washington.edu/files/2021-FastLabels-VIS.pdf
- https://journals.scholarpublishing.org/index.php/BJHR/article/download/4445/2763/11691
