---
name: anatomy-3d-viewer
version: "1.0.0"
description: Complete working Three.js 3D anatomy viewer with Spanish/English bilingual support, system layers, orbit controls, and info panels. Drop-in reference for SOMA's body model.
trigger: When building or referencing 3D anatomy visualization components
---

# 3D Anatomy Viewer Reference

Complete self-contained HTML/Three.js anatomy viewer with:
- 5 body systems (cardiovascular, nervous, respiratory, musculoskeletal, digestive)
- Orbit controls for rotation/zoom
- Layer toggling (skin, muscle, bone, organs)
- Bilingual info panels (Spanish/English)
- Procedural organ geometry (heart, brain, lungs, skeleton, digestive)

See references/anatomy-atlas.html for the full 437-line implementation.

Key patterns to extract for SOMA:
1. System-based scene organization (each body system = group of meshes)
2. Bilingual data structure (name/nameEs pairs)
3. Layer visibility toggling
4. Click-to-select with raycasting + info panel
5. Responsive sidebar with system buttons

## Browser Dev Mode Bypass (Critical for Testing)

Tauri apps can't run in a regular browser. When testing via Browserbase/cloudflare tunnel, you MUST bypass auth + onboarding. This took extensive trial-and-error to get right.

### What DOES NOT Work
- `browser_type` on React controlled inputs -- sets DOM value but onChange never fires, so React state stays empty. The form submit button will be disabled.
- Setting localStorage inside `useEffect` -- hooks that read localStorage (like `useUserDemographics`) may have already read `false` before your useEffect runs.
- Using underscores in localStorage keys -- SOMA uses DASHES: `soma-browser-db-exists` not `soma_browser_db_exists`.

### What WORKS
1. Set localStorage **synchronously in component body** (NOT useEffect) BEFORE any hooks read it:
```tsx
const isBrowserDev = typeof window !== 'undefined' && !(window as any).__TAURI_INTERNALS__;
if (isBrowserDev && localStorage.getItem('soma-browser-db-exists') !== 'true') {
  localStorage.setItem('soma-browser-db-exists', 'true');
  localStorage.setItem('biological-self-onboarded', 'true');
}
```
2. Set React state in a separate useEffect guarded by useRef (prevents StrictMode double-fire):
```tsx
const devBypassDone = useRef(false);
useEffect(() => {
  if (isBrowserDev && !devBypassDone.current) {
    devBypassDone.current = true;
    setHasDatabase(true);
    setUnlocked(true);
    setLoading(false);
  }
}, [isBrowserDev]);
```

### SOMA-Specific localStorage Keys (use DASHES)
- `soma-browser-db-exists` -- checked by tauri-invoke.ts mock for `check_database_exists`
- `biological-self-onboarded` -- checked by `useUserDemographics` hook (ONBOARDED_KEY)
- `biological-self-demographics` -- cached user demographics JSON

### Tauri Internals Detection
```tsx
const isTauri = !!(window as any).__TAURI_INTERNALS__;
```

### Cloudflare Tunnel for Browser Testing
Browserbase can't reach localhost. Use cloudflared:
```bash
cloudflared tunnel --url http://localhost:1420 2>&1 &
# Capture the trycloudflare.com URL from the logs
```
Tunnel URL changes on every restart -- always grab the new one.

## Annotation Click → Radial Menu Pipeline (Critical Pitfall)

### The Problem
Clicking body part labels (Cráneo, Corazón, etc.) on the 3D model did NOT open the radial context menu. Clicks were silently swallowed with no error.

### Root Cause
The event chain is: `AnnotationLabel.onClick` → `onAnnotationClick(id)` → `handleEnhancedStructureSelect(id, name)`. The annotation click handler only passes the annotation ID, NOT the mouse event or screen coordinates. But `handleEnhancedStructureSelect` has a guard:

```tsx
// AnatomyViewer.tsx line 1011
if (onStructureSelect && event) {
  onStructureSelect(structureId, structureName, screenPosition);
}
```

Since no `event` was passed, `onStructureSelect` (which triggers the radial menu in `BodyCentricHome`) was **never called**. The function returned after just setting internal state.

### The Fix
Project the annotation's 3D position to approximate screen pixel coordinates:

```tsx
onAnnotationClick={(id: string) => {
  const annotation = ANATOMY_ANNOTATIONS.find(a => a.id === id);
  if (annotation) {
    const name = language === 'es' ? annotation.labelEs : annotation.labelEn;
    // Project 3D position to screen (model centered in viewport)
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const screenX = vw / 2 + (annotation.position[0] * vw * 0.35);
    const screenY = vh / 2 - (annotation.position[1] * vh * 0.35);
    handleEnhancedStructureSelect(id, name, { x: screenX, y: screenY });
  }
}}
```

### Why This Happens
React Three Fiber's `AnnotationLayer` renders HTML label overlays. Clicks on these HTML elements don't carry Three.js `ThreeEvent` data (no `nativeEvent.clientX`). The click handler only receives the annotation ID. To get screen coordinates, you must compute them from the annotation's known 3D position.

### General Lesson for R3F Apps
When R3F annotations/labels are HTML overlays (not 3D meshes), click events lose the Three.js event context. Any handler that needs screen position must:
1. Receive it as a separate parameter, OR
2. Project the known 3D position to screen coordinates using camera/viewPort math

Never assume `ThreeEvent` or native `MouseEvent` will be available through the full callback chain.
