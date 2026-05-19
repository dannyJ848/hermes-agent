# 3d-annotation-techniques-threejs-vlfm

*Researched: 2026-04-05 02:19 CDT*

# 3D Annotation Techniques: Three.js + Vision-Language Foundation Models

## Date: 2025-04-05
## Domain: VISION (Cycle 14)

---

## Finding 1: Three.js WebGL Annotation Best Practice (manu.ninja)

**Key technique:** Use DOM overlays, NOT WebGL text rendering, for annotations.

**Architecture:**
1. Define annotation anchor as `THREE.Vector3(x, y, z)` in model space
2. Project to NDC via `vector.project(camera)`
3. Convert NDC to screen coordinates:
```js
vector.x = Math.round((0.5 + vector.x / 2) * (canvas.width / window.devicePixelRatio));
vector.y = Math.round((0.5 - vector.y / 2) * (canvas.height / window.devicePixelRatio));
```
4. Position HTML/CSS annotation elements at those coordinates
5. Update on every camera change (orbit, zoom, pan)

**Why DOM over WebGL:**
- Browser handles typography and layout far better than WebGL
- CSS styling (borders, shadows, animations) is free
- Click/hover events work natively
- No texture atlas or font rendering needed

**For SOMA:** This is the exact pattern for anatomy labels. Each anatomical structure gets a Vector3 anchor point. Labels project to 2D and render as styled HTML divs. Lines connect labels to structures via CSS `::before` pseudo-elements or SVG overlays.

**Pitfall:** Labels can overlap when structures are close. Need collision avoidance / label spreading algorithm.

---

## Finding 2: Vision-Language Foundation Models for 3D Medical Imaging (Nature, Aug 2025)

**Paper:** "Vision-language foundation model for 3D medical imaging" — Wu et al., npj Artificial Intelligence, Vol 1, Article 17

**Key insights:**
- Reviews 23 studies on VLFMs for radiology report generation from 3D imaging (CT, MRI)
- VLFMs combine image processing + NLP to mimic radiologist analysis
- Major challenge: producing consistent, high-quality reports from 3D volumes
- Critical need for diverse training datasets and standardized evaluation metrics
- Global radiologist shortage makes automated reporting increasingly important

**Relevant to SOMA:**
- If SOMA captures 3D anatomy screenshots, a VLFM could auto-generate descriptions
- Bilingual (EN/ES) report generation aligns with SOMA's medical education mission
- Architecture: Screenshot → VLM → structured anatomical description in chosen language

---

## Finding 3: Visual Prompts on Anatomical Structures (MICCAI 2025)

**Paper:** "Your other Left! Vision-Language Models Fail to Identify..." — investigates visual prompts (alphanumeric/colored markers) on anatomy

**Key concept:** Placing numbered markers (Set-of-Mark style) on anatomical structures and asking VLMs to identify them. Directly applicable to:
- SOMA's interactive anatomy quiz mode
- Automated structure identification from 3D renders
- Grounding VLM responses to specific model regions

**Integration path for SOMA:**
1. Render 3D anatomy model with numbered markers at structure centroids
2. Capture screenshot
3. Send to VLM with prompt: "Identify each numbered structure. Provide name in English and Spanish."
4. Validate against SOMA's anatomy database
5. Generate quiz questions from the results

---

## Action Items for SOMA Codebase
1. Implement `AnatomyLabel` component using the DOM overlay projection pattern
2. Add collision avoidance for overlapping labels (greedy overlap removal)
3. Research label spreading algorithms (active literature: map labeling, point-feature labeling)
4. Consider VLM integration for auto-generating structure descriptions


## Sources

- https://manu.ninja/webgl-three-js-annotations/
- https://www.nature.com/articles/s44387-025-00015-9
- https://papers.miccai.org/miccai-2025/paper/0530_paper.pdf
