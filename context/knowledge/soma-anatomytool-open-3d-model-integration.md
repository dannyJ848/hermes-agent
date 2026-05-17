# SOMA AnatomyTOOL Open 3D Model Integration

*Researched: 2026-04-04 21:41 CDT*

# AnatomyTOOL Open 3D Model — SOMA Integration Opportunity

## Source
- **URL**: https://anatomytool.org/open3dmodel
- **License**: Creative Commons Attribution ShareAlike (CC BY SA)
- **Creators**: Departments of Anatomy at Leiden UMC, UMC Utrecht, Maastricht UMC, KU Leuven, Amsterdam UMC, Radboud UMC, University of Gent
- **Funding**: Dutch Ministry of Education, Culture & Science

## Current State (April 2026)
- Complete skeleton including skull (July 2025)
- Upper limb (July 2025)
- Lower limb (July 2025)
- Pelvis and perineum (December 2025)
- Inguinal canal (January 2026)
- Muscles of thorax, abdomen and back (March 2026)

## Technical Details
- Based on predecessor models: BodyParts3D and Z-Anatomy
- Sub-models directly usable in browser: https://anatomytool.org/open3dmodel-learn
- Source files and selection models: https://anatomytool.org/open3dmodel-create
- Models are Blender-compatible → exportable to glTF/GLB for Three.js

## SOMA Integration Strategy
1. **glTF/GLB Export**: Models from Blender can be exported as .glb files, directly loadable by Three.js GLTFLoader
2. **Layer System**: Already organized by anatomical system (skeleton, muscles, organs, vessels)
3. **Bilingual Potential**: CC BY SA allows adaptation → add EN/ES labels
4. **Mobile-Ready**: WebGL/Three.js models work in WKWebView for iOS
5. **Sub-model Architecture**: Use topic-specific sub-models for progressive disclosure

## Action Items for SOMA
- [ ] Download source files from anatomytool.org/open3dmodel-create
- [ ] Convert key sub-models to optimized GLB (Draco compression)
- [ ] Build ZAnatomyLoader compatible with existing SOMA architecture
- [ ] Map structure names to bilingual EN/ES terminology
- [ ] Integrate with SOMA's existing layer toggle system

## Related
- Z-Anatomy: https://z-anatomy.com (Blender-based, also CC BY SA)
- BodyParts3D: Original Japanese anatomical database
- Three.js anatomy forum: https://discourse.threejs.org (active community)


## Sources

- https://anatomytool.org/open3dmodel
- https://discourse.threejs.org/t/a-3d-interactive-system-for-exploring-human-anatomy-by-anatomical-layers/88813
