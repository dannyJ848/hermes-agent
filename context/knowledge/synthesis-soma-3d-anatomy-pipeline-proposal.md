# synthesis-soma-3d-anatomy-pipeline-proposal

*Researched: 2026-04-02 22:07 CDT*

# Synthesis: SOMA 3D Anatomy Pipeline — Integration Proposal

*Synthesized: 2026-04-02 22:00 CDT*
*Sources: 10 findings across 3D rendering, anatomy datasets, WebGPU, FHIR, medical AI*

## Executive Summary

SOMA has all the researched components to build a "Complete Anatomy"-quality 3D viewer. This proposal connects 5 independent research threads into a single implementation roadmap.

## Source Findings Matrix

| Finding | Domain | Key Insight |
|---------|--------|-------------|
| open-source-3d-anatomy-models-2026 | Datasets | Z-Anatomy (CC-BY-SA 4.0, 11 systems, 2-5M polys) is the primary source |
| webgpu-sss-shaders-anatomy-2026 | Rendering | Pre-integrated SSS via TSL nodes, tissue-specific parameters |
| soma-3d-anatomy-rendering-deep-dive | Rendering | Cross-section stencil capping, 6 tissue shader patterns |
| threejs-webgpu-migration-2026 | Platform | One-line migration to WebGPURenderer, 95% browser coverage |
| browser-medical-image-segmentation | AI/ML | MobileSAM (40MB) for on-device organ segmentation |
| soma-fhir-to-3d-mapping-architecture | Data | SNOMED CT → body region mapping, lab-to-region inference |
| webgpu-compute-medical-visualization | Compute | GPU Marching Cubes, Direct Volume Rendering via WGSL |

## Cross-Domain Patterns Identified

### Pattern 1: Enabling Technology Chain (HIGH VALUE)
```
Z-Anatomy GLBs → Meshopt LOD (10-25x compression) → WebGPURenderer → 
TSL SSS Nodes → FHIR bodySite overlay → Interactive 3D anatomy
```
Each research finding enables the next. The full chain is:
1. **Z-Anatomy** provides the mesh data (Blender → GLB export)
2. **Meshopt** compresses 2-5M triangles to &lt;200K for mobile
3. **WebGPURenderer** enables compute shaders + TSL
4. **TSL SSS** gives tissue-realistic rendering (skin, muscle, organ, bone)
5. **FHIR mapping** overlays patient health data on the 3D model
6. **Result**: Interactive 3D body with health data visualization

### Pattern 2: Performance Budget Alignment (HIGH CONFIDENCE)
All research converges on the same budget:
- **200K triangles** mobile target (Z-Anatomy LOD research)
- **~2ms SSS** on Apple M1 at 1080p (Jimenez separable blur)
- **&lt;100 draw calls** with instancing (Three.js best practices)
- **&lt;200MB GPU** memory (iOS WKWebView limit)
- **30 FPS minimum** on iPhone 14

### Pattern 3: Graceful Degradation Path
```
WebGPU (desktop) → WebGL2 (fallback) → Static images (low-end)
SSS (high-end) → Pre-integrated LUT (mid) → Lambert (low-end)
SAM segmentation (desktop) → Server-side API (mobile) → None (offline)
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal:** Z-Anatomy GLBs loading in SOMA with basic rendering

1. Export Z-Anatomy Blender file to GLB per system (skeletal, muscular, organs, etc.)
2. Implement ZAnatomyLoader.ts with LOD via Meshopt decoder
3. Wire into existing `WebGPUAnatomyCanvas.tsx`
4. Basic layer toggle (11 systems)
5. Verify: `npx tsc --noEmit` passes, model loads at 30 FPS

**Dependencies:** Blender for export, meshopt_decoder.ts, three/webgpu r171+
**Risk:** GLB export quality from Blender — may need manual cleanup

### Phase 2: Visual Quality (Week 3-4)
**Goal:** Tissue-realistic rendering with SSS

1. Create SubsurfaceScatteringTSL.ts with per-tissue profiles
2. Implement pre-integrated SSS LUT (128x128, 3-lobe Gaussian)
3. Add tissue type metadata to GLB user data
4. Screen-space SSS as optional post-processing pass
5. KTX2 texture compression for all maps

**Dependencies:** TSL knowledge from findings, KTX2 tools
**Risk:** TSL API stability — Three.js r182+ may change node API

### Phase 3: Health Data Overlay (Week 5-6)
**Goal:** FHIR resources visualized on 3D body

1. Implement FHIR → SNOMED CT → body region mapping
2. Color-coded health indicators on affected regions
3. Lab-to-region inference (BNP→Heart, eGFR→Kidney)
4. Medication-to-region pharmacological overlay
5. Bilingual labels (EN/ES) via BilingualTerminology.ts

**Dependencies:** FhirAdapter.ts (exists), BilingualTerminology.ts (exists, 45 terms)
**Risk:** SNOMED CT code coverage — need 200+ codes for full body mapping

### Phase 4: Interactive Features (Week 7-8)
**Goal:** Cross-sections, dissection, radial menus

1. Stencil buffer capping for cross-section rendering
2. Clipping plane UI (6 orientations)
3. Radial context menu on region selection
4. "My Health" / "Education" branch navigation
5. Touch gesture support for mobile

**Dependencies:** Cross-section research from deep-dive finding
**Risk:** Stencil buffer on iOS WKWebView — may need fallback

## Competitive Advantage Analysis

| Feature | Complete Anatomy | BioDigital | SOMA (Proposed) |
|---------|-----------------|------------|-----------------|
| Price | $150/yr | $48/yr | **Free + Open Source** |
| Bilingual EN/ES | ❌ | ❌ | ✅ Built-in |
| Patient Health Data | ❌ | ❌ | ✅ FHIR integration |
| Open Source Models | ❌ | ❌ | ✅ Z-Anatomy CC-BY-SA |
| Mobile Performance | Native | Web | WebGPU/WebGL |
| SSS Rendering | ✅ Native | ❌ | ✅ TSL + WebGPU |

**SOMA's unique position:** Only free, bilingual, health-data-integrated 3D anatomy platform.

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| WebGPU not on iOS Safari | Low (Safari 26+ has it) | High | WebGL2 fallback with reduced SSS |
| Z-Anatomy GLB export issues | Medium | Medium | Manual Blender cleanup + BodyParts3D backup |
| 200K tri budget too aggressive | Low | Medium | Progressive loading, LOD streaming |
| CC-BY-SA copyleft concerns | Low | Low | Proper attribution in app |
| TSL API breaking changes | Medium | Medium | Pin Three.js version, test before upgrade |

## Success Metrics

- [ ] Z-Anatomy GLBs load in &lt;3 seconds on mobile
- [ ] 30 FPS sustained with SSS on iPhone 14
- [ ] All 11 anatomical systems toggleable
- [ ] FHIR Condition resources display on correct body regions
- [ ] Bilingual labels render correctly for all visible anatomy
- [ ] Cross-sections render with stencil capping
- [ ] Total bundle size &lt;50MB (compressed GLBs + textures)


## Sources

- open-source-3d-anatomy-models-2026.md
- webgpu-sss-shaders-anatomy-2026.md
- soma-3d-anatomy-rendering-deep-dive.md
- threejs-webgpu-migration-2026.md
- browser-medical-image-segmentation.md
- soma-fhir-to-3d-mapping-architecture.md
- webgpu-compute-medical-visualization.md
