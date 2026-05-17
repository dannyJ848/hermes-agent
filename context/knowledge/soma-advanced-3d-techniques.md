# soma-advanced-3d-techniques

*Researched: 2026-04-02 13:50 CDT*

# SOMA Advanced 3D Techniques Research (April 2026)

## Thickness Map Baking in Blender (SSS prerequisite)

Process for creating SSS thickness maps per organ:
1. Select organ mesh in Blender
2. Create Emissive shader → add Input > Ambient Occlusion node
3. Check "Inside" and "Only Local" on AO node
4. Set distance (0.2-0.6 depending on organ size — ears thin, liver thick)
5. Apply scale first (Ctrl+A > Scale) — CRITICAL or AO distance is wrong
6. Bake to texture (Cycles render engine required)
7. Invert: white = thin (ears, skin flaps), black = thick (bone, dense organs)
8. Export as grayscale PNG, convert to KTX2 for mobile

Blender Stack Exchange: https://blender.stackexchange.com/questions/100724/
Jim Morren tip: use Geometry > Pointiness node overlaid for blood vessel detail in thickness map

## Transparent Sorting in Three.js (layer system)

Three.js sorts transparent objects automatically by distance, but only per-object, not per-pixel. This means overlapping transparent organs can look wrong.

Solution: renderOrder property on each layer group:
- skeleton: renderOrder 1 (behind everything)
- organs: renderOrder 2
- muscles: renderOrder 3
- vessels: renderOrder 5
- skin: renderOrder 10 (in front of everything)

CRITICAL: depthWrite must be false for transparent materials. depthTest stays true. This is the #1 source of visual bugs in anatomy viewers.

Limit to 2 transparent layers on mobile (e.g., skin + one organ layer). 3+ causes severe overdraw and iOS crashes.

## Draw Call Reduction Strategies

Anatomy model has 200+ separate meshes. Each = 1 draw call. Mobile budget = 100.

Approaches:
1. **Merge static geometry**: BufferGeometryUtils.mergeGeometries() for all bones (same material). Reduces 206 bones → 1 draw call.
2. **InstancedMesh**: For repeated geometry (vertebrae, ribs, teeth). One geometry + N transforms = 1 draw call.
3. **Texture atlases**: Combine all bone textures into one atlas. Share material across all bones.
4. **Material sharing**: Same MeshStandardMaterial instance for all bones, another for all organs.
5. **LOD culling**: Hide organs not visible from current camera angle.

Target: 200+ meshes → ~20-30 draw calls after optimization.

## BVH Raycasting Details (three-mesh-bvh)

API:
```typescript
import { computeBoundsTree, acceleratedRaycast } from 'three-mesh-bvh';
THREE.BufferGeometry.prototype.computeBoundsTree = computeBoundsTree;
THREE.Mesh.prototype.raycast = acceleratedRaycast;

// Build after model loads
mesh.geometry.computeBoundsTree();

// Raycast as normal — automatic BVH acceleration
raycaster.intersectObjects(scene.children);
```

Memory overhead: ~10-20% per geometry. Build time: ~100ms for 100K triangles.
Must rebuild if geometry changes. Static anatomy = build once.
For skinned/animated: use refit instead of full rebuild (faster).

## R3F Event Propagation (selection vs OrbitControls)

The core conflict: OrbitControls captures ALL pointer events on the canvas. Organ selection also needs pointer events.

Solution hierarchy:
1. Interactive organ meshes use onPointerDown
2. Inside handler: e.stopPropagation() — prevents OrbitControls from receiving the event
3. Result: tapping an organ = selection. Tapping empty space = OrbitControls rotation.

From sbcode.net R3F tutorial: stopPropagation also prevents events from reaching meshes behind the current one. This means if skin is over an organ, skin's handler fires first. Must design selection so skin is only interactive when visible AND not in X-ray mode.

## WebGL Memory Management (iOS crash prevention)

iOS WKWebView kills the process silently when GPU memory exceeds ~350MB. No error thrown.

Rules for SOMA:
1. Dispose EVERYTHING when switching layers: geometry.dispose(), material.dispose(), texture.dispose()
2. Remove meshes from scene before disposing (scene.remove(mesh))
3. Null references after dispose (mesh = null) to allow GC
4. Track texture memory: sum of width*height*4 bytes per texture
5. Use texture pooling for frequently loaded/unloaded organs
6. Compress textures to KTX2 (ETC2 on mobile, ASTC on iOS)
7. Monitor with renderer.info.memory.textures, renderer.info.memory.geometries

iOS-specific: Safari WebContent process has ~350MB hard limit. Renderer.info.render.calls shows draw calls. Keep total GPU memory under 200MB.

## Post-Processing on Mobile

ACES Filmic tone mapping: renderer.toneMapping = THREE.ACESFilmicToneMapping. Free (no extra pass). Makes medical visualization look more natural.

Bloom: 2 extra render passes. Use sparingly — only for SSS glow on selected organ, not global. Mobile cost: ~3-5ms per frame.

Recommendation: Enable ACES tone mapping always. Enable bloom only on high-tier devices. Disable all post-processing on low-tier.

## Anatomy Metadata Standards

Foundational Model of Anatomy (FMA) ontology: standardized IDs for every anatomical structure. ~75,000 concepts. Available at bioportal.bioontology.org/ontologies/FMA.

SOMA should use FMA IDs as canonical organ identifiers:
- FMA:5084 = Heart
- FMA:7203 = Liver  
- FMA:7197 = Right Kidney
- FMA:7198 = Left Kidney
- FMA:46598 = Cerebral Cortex

This enables interoperability with BioMCP, medical databases, and ICD-10 mapping.

## Blender Batch Export for Anatomy

Command-line glTF export:
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b anatomy.blend \
  --python export_gltf.py -- --output_dir ./models/
```

Python script iterates collections (skeleton, muscles, organs, vessels, nerves, skin), exports each as separate .glb with proper materials.

gltf-transform post-processing:
```bash
gltf-transform optimize organ.glb organ-optimized.glb \
  --compress meshopt \
  --texture-compress ktx2 \
  --simplify --simplify-error 0.005
```

## Medical Video Content Sources

Open-access medical video for SOMA's education content:
- Crash Course Anatomy & Physiology (YouTube, CC BY)
- OLI Anatomy & Physiology (CMU Open Learning Initiative)
- AnatomyTOOL videos (university-produced, open access)
- HEAL (Human Embryology Animations)
- OpenStax Anatomy & Physiology (free textbook + media)

Content pipeline: source video → FFmpeg trim/compress → 720p MP4 + WebM → 15-60s clips → thumbnail extraction → metadata JSON

