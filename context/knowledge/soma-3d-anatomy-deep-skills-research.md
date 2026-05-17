# soma-3d-anatomy-deep-skills-research

*Researched: 2026-04-02 13:45 CDT*

# SOMA 3D Anatomy: Complete Technical Deep-Dive (April 2026)

## 10 Domains Required to Build Complete Anatomy-Level Visualization

### 1. GLSL SHADER PROGRAMMING

**SSS Shader Types for Anatomy:**
- Fast SSS (Penner SIGGRAPH 2011): thickness map + distortion/power/scale/ambient params. Ships in Three.js as SubsurfaceScatteringShader.js
- Pre-integrated SSS: cheapest approach for mobile. Uses baked thickness texture (1-channel grayscale)
- Screen-Space SSS (Jorge Jimenez): blurs lighting buffer, more accurate but needs render-to-texture. High-end only.

**Per-Organ SSS Params:**
| Organ | distortion | power | scale | ambient | Interior color |
|-------|-----------|-------|-------|---------|---------------|
| Skin | 0.1 | 2.0 | 2.0 | 0.1 | peach |
| Heart | 0.3 | 3.0 | 3.0 | 0.2 | dark red |
| Liver | 0.4 | 2.5 | 4.0 | 0.3 | brown-red |
| Lungs | 0.2 | 2.0 | 2.5 | 0.1 | pink |
| Kidney | 0.3 | 3.0 | 3.0 | 0.2 | dark red |
| Stomach | 0.3 | 2.5 | 3.0 | 0.2 | pink-tan |
| Brain | 0.5 | 2.0 | 3.5 | 0.3 | pink-gray |
| Bone | 0.0 | — | — | — | ivory (no SSS) |

**Fresnel/X-Ray Shader:** `float fresnel = pow(1.0 - abs(dot(viewDir, normal)), fresnelPower);` + depthWrite:false + transparent:true

**Shader Pitfalls:** mediump precision on mobile, guard SSS code with #ifdef, dispose materials to prevent GPU leaks, iOS Safari shader compilation limit

### 2. CLIPPING PLANES + STENCIL CAPPING

Three clipping orientations: Axial/Plane(0,-1,0), Sagittal/Plane(1,0,0), Coronal/Plane(0,0,-1)

Stencil algorithm: (1) render back faces, increment stencil where clip passes (2) render front faces, decrement (3) stencil != 0 inside volume (4) render cap plane with stencil test + interior color

Three.js reference: webgl_clipping_stencil.html example

### 3. DUAL-SCENE X-RAY REVEAL (Codrops March 2026)

Architecture: Scene A (solid skin) + Scene B (X-ray Fresnel) render to separate RTs. Fluid sim masks blend point. Ping-pong render targets alternate each frame. FBM noise diffuses mouse trail.

SOMA simplified version: circular gradient mask expanding from tap point, no fluid sim needed.

### 4. BVH RAYCASTING (gkjohnson/three-mesh-bvh, 3.3K stars)

Reduces raycast from O(n) to O(log n). 200ms → 0.5ms for 500K triangles. Build once on load for static anatomy. Two-level approach: (1) coarse bbox raycast for organ ID, (2) fine BVH raycast for exact point.

### 5. SELECTION HIGHLIGHT OPTIONS

A. @react-three/postprocessing Outline (best quality, 2 extra passes)
B. Inverted-hull outline (cheapest, scale 5% + BackSide + solid color) — recommended for mobile
C. Custom shader outline (fwidth() edge detection in fragment shader)

### 6. RADIAL MENU

Motion (Framer Motion) has exact example at motion.dev/examples/react-radial-menu. Staggered spring animations. Position via worldToScreen() projection. R3F Drei Html component bridges 3D to 2D DOM.

Edge cases: near-screen-edge → flip direction, during rotation → update position or dismiss, covers organ → offset 80px opposite camera.

### 7. LAYER TOGGLE

Each body system = separate Three.js Group. Toggle = group.visible. Transparency requires renderOrder (skin=10, vessels=5, muscles=3, organs=2, skeleton=1). Max 2 transparent layers on mobile.

### 8. VIDEO-FIRST CONTENT

NOT VideoTexture. Fullscreen HTML5 video overlay. Format: MP4 H.264 (iOS) + WebM VP9 (Android), 720p max (4K crashes iOS), 1-2Mbps, 15-60s clips. Muted autoplay required on iOS. TikTok-style vertical swipe UX. EN/ES toggle per video.

### 9. ASSET SOURCES

Z-Anatomy (SimTK): CC BY SA, 5000+ structures, Blender format. PRIMARY SOURCE.
AnatomyTOOL Open3D: CC BY SA, university-grade, skeleton+muscles done, actively developed.
BodyParts3D: CC BY SA, older but comprehensive.

Pipeline: Z-Anatomy .obj → Blender (assign materials, bake thickness/AO/normal maps, UV maps, body system groups) → gltf-transform (Meshopt+KTX2, 4 LOD levels) → @needle-tools/gltf-progressive

### 10. RENDER PIPELINE (33ms budget for 30fps)

Input(2ms) → Depth pre-pass(1ms) → Opaque pass(12ms) → Translucent pass(5ms) → Selection(2ms) → Post-processing(2ms) → UI overlay(2ms) → Video overlay(6ms)

## Learning Order
Phase 1 (Week 1-2): GLSL basics, Three.js materials, R3F events, Z-Anatomy in Blender
Phase 2 (Week 3-4): SSS shader, thickness map baking, clipping+stencil, layer toggle
Phase 3 (Week 5-6): BVH raycast, selection+outline, radial menu, touch gestures
Phase 4 (Week 7-8): X-ray reveal, progressive loading, video pipeline, mobile optimization


## Sources

- https://therealmjp.github.io/posts/sss-intro/
- https://www.slideshare.net/slideshow/penner-preintegrated-skin-rendering-siggraph-2011-advances-in-realtime-rendering-course/13966747
- https://gist.github.com/mattdesl/2ee82157a86962347dedb6572142df7c
- https://github.com/gkjohnson/three-mesh-bvh
- https://tympanus.net/codrops/2026/03/23/building-a-dual-scene-fluid-x-ray-reveal-effect-in-three-js/
- https://motion.dev/examples/react-radial-menu
- https://simtk.org/projects/z-anatomy
- https://anatomytool.org/open3dmodel
- https://80.lv/articles/building-an-anatomical-system-using-zbrush-blender
