---
name: soma-3d-anatomy-complete-blueprint
version: 1.0
created: 2026-04-02
description: Complete technical blueprint for building SOMA's 3D anatomy visualization at Complete Anatomy (3D4Medical) quality levels. Covers every shader technique, interaction pattern, asset pipeline, and pitfall. This is the master reference before writing any code.
tags: [soma, 3d, anatomy, shaders, sss, glsl, three.js, r3f, medical, clipping, raycasting, video, radial-menu]
---

# SOMA 3D Anatomy Complete Blueprint

## UX: The Body IS the Interface

User opens app → 3D body with SSS skin (rotating, no menus, no buttons)
→ Tap anywhere → organ highlights with pulse ring animation (<100ms)
→ Radial menu appears at tap point (animated, spring physics)
→ 6 options: Education (videos), My Health, Conditions, Medications, Layers, Cross-Section

**Core rule: ZERO text walls. Everything is video, image, or 3D interaction.**

## 10 Technical Domains

### 1. GLSL Shader Programming

**SSS Shader (subsurface scattering)** — makes organs look alive, not plastic
- Three.js built-in: `three/addons/shaders/SubsurfaceScatteringShader.js`
- Uses thickness map (baked inverted AO in Blender) + 4 params per organ
- Per-organ tuning is the secret sauce (see knowledge file for param table)

**Fresnel/X-Ray Shader** — see-through mode for peeling layers
```glsl
float fresnel = pow(1.0 - abs(dot(viewDir, normal)), fresnelPower);
// + depthWrite: false + transparent: true
```

**Stencil Cap Shader** — fills hollow cross-sections with interior color
- Three.js example: `webgl_clipping_stencil.html`
- Algorithm: back faces increment stencil, front faces decrement, cap renders where stencil != 0

**Pitfalls:** mediump on mobile, dispose materials, iOS shader limit

### 2. Clipping Planes + Cross-Sections

```typescript
const axialPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), offset);
material.clippingPlanes = [axialPlane];
renderer.localClippingEnabled = true;
```
Three orientations: Axial, Sagittal, Coronal. Stencil buffer must be enabled. Per-organ interior colors.

### 3. Dual-Scene X-Ray Reveal (Codrops March 2026)

Scene A (solid) + Scene B (X-ray Fresnel) → separate render targets → fluid mask blend.
SOMA simplified: circular gradient mask expanding from tap, no fluid sim.

### 4. BVH Raycasting (three-mesh-bvh, 3.3K stars)

```typescript
import { acceleratedRaycast, computeBoundsTree } from 'three-mesh-bvh';
THREE.BufferGeometry.prototype.computeBoundsTree = computeBoundsTree;
// Build once after loading, reduces raycast from 200ms to 0.5ms
```

### 5. Selection Highlight

- **Mobile**: inverted-hull outline (clone mesh, scale 5%, BackSide, solid color, pulse animation)
- **Desktop**: @react-three/postprocessing Outline (2 extra passes, higher quality)

### 6. Radial Menu (Motion/Framer Motion)

```tsx
import { Html } from '@react-three/drei';
// Position HTML overlay at 3D point via worldToScreen()
// Motion staggered spring animations
// 44x44pt minimum tap targets (Apple HIG)
```
Edge cases: flip near screen edges, dismiss on camera rotation, offset from organ

### 7. Layer Toggle

Each body system = Three.js Group. Toggle = `group.visible`.
renderOrder for transparency: skin(10) > vessels(5) > muscles(3) > organs(2) > skeleton(1)
Max 2 transparent layers on mobile.

### 8. Video-First Content

NOT VideoTexture (4K crashes iOS). Fullscreen HTML5 overlay.
Format: MP4 H.264 + WebM VP9, 720p max, 1-2Mbps, 15-60s.
Muted autoplay required on iOS. TikTok-style vertical swipe.

### 9. Asset Sources & Pipeline

- **Z-Anatomy** (CC BY SA): 5000+ structures, Blender format — PRIMARY
- **AnatomyTOOL Open3D** (CC BY SA): University-grade, actively developed
- **BodyParts3D** (CC BY SA): Older but comprehensive

Pipeline: Z-Anatomy .obj → Blender (materials, bake thickness/AO, UV, system groups) → gltf-transform (Meshopt+KTX2, 4 LODs) → @needle-tools/gltf-progressive

### 10. Render Pipeline (33ms budget @ 30fps)

Input(2ms) → Depth pre-pass(1ms) → Opaque(12ms) → Translucent(5ms) → Selection(2ms) → Post(2ms) → UI(2ms) → Video(6ms)

## Learning Order

Phase 1 (Wk 1-2): GLSL basics, Three.js materials, R3F events, Z-Anatomy in Blender
Phase 2 (Wk 3-4): SSS shader, thickness baking, clipping+stencil, layer toggle
Phase 3 (Wk 5-6): BVH raycast, selection, radial menu, touch gestures
Phase 4 (Wk 7-8): X-ray reveal, progressive loading, video pipeline, mobile perf

## Critical References

- Penner SSS: SIGGRAPH 2011 Advances in Real-Time Rendering
- Matt DesLauriers SSS Gist: github.com/mattdesl/2ee82157a86962347dedb6572142df7c
- three-mesh-bvh: github.com/gkjohnson/three-mesh-bvh
- Codrops X-Ray: tympanus.net/codrops/2026/03/23/building-a-dual-scene-fluid-x-ray-reveal-effect-in-three-js/
- Motion Radial Menu: motion.dev/examples/react-radial-menu
- Z-Anatomy: simtk.org/projects/z-anatomy
- AnatomyTOOL: anatomytool.org/open3dmodel
- The Book of Shaders: thebookofshaders.com

## Asset Pipeline

DICOM/NIfTI → segmentation → mesh generation → decimation → glTF export → Three.js loading.

**Tools:** 3D Slicer (segmentation), Blender (cleanup/decimation), glTF Validator.
**Pitfalls:** DICOM orientation (LPS vs RAS), Z-Anatomy license (CC-BY-NC), decimation ratio (keep 30-50% for organs).

## Bilingual Medical Terms

EN/ES terminology mapping for SOMA's UI and content. Maps standard anatomical terms to Spanish equivalents with regional variants.

Example mappings:
- Heart → Corazón
- Liver → Hígado
- Brain → Cerebro
- Kidney → Riñón

## Cross-Sections & Dissection

Interactive cross-sections using clipping planes + stencil buffer:
- Three orientations: Axial, Sagittal, Coronal
- Per-organ interior colors
- Stencil cap shader fills hollow sections

## Encyclopedia Entries

Medical encyclopedia seed data structure for SOMA's "Education" branch:
- Organ overview (video + 3D model)
- Common conditions
- Medications affecting the organ
- Procedures and surgeries

## Citation Type System

TypeScript citation types for medical content attribution:
- `Citation` interface with source, url, confidence, date_verified
- Used throughout SOMA's data layer for evidence-based content

## Mobile 3D Rendering

Advanced mobile rendering considerations:
- WebGL2 on iOS WKWebView
- Metal-backed rendering performance
- Touch gesture handling for 3D rotation
- Memory-constrained mesh loading
