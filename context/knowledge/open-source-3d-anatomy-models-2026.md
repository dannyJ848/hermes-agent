# open-source-3d-anatomy-models-2026

*Researched: 2026-04-02 20:05 CDT*

# Open-Source 3D Anatomy Models for SOMA (April 2026)

## Executive Summary

| Dataset | Full Body? | Format | License | Layered? | Est. Polygons | Active? |
|---------|-----------|--------|---------|----------|---------------|---------|
| **Z-Anatomy** | ✅ Yes | .blend → glTF/OBJ | CC-BY-SA 4.0 | ✅ 11 systems | 2-5M total | ✅ Active |
| **BodyParts3D** (DBCLS) | ✅ Yes | OBJ (+ VRML, STL) | CC-BY-SA 2.1 JP | ✅ 5+ systems | 3-8M total | ⚠️ Maintenance |
| **OpenAnatomy** (Harvard) | ⚠️ Partial | MRB/NRRD (voxel) | CC-BY (mostly) | ⚠️ Region-specific | Voxel-based | ✅ Active |
| **Visible Human** derivatives | ✅ Yes | STL, OBJ, PLY | Public Domain | ✅ | 1-10M+ | ⚠️ Varies |

## Z-Anatomy (Recommended Primary Source)
- **Source:** github.com/michaelantoniomcnally/Z-Anatomy
- **Best option for SOMA** — single coherent model, all parts proportionally correct
- 11 anatomical systems as Blender collections (easy layer toggle)
- Named objects with Latin nomenclature
- Export pipeline: .blend → Blender → glTF/GLB with object hierarchy preserved
- CC-BY-SA 4.0 (copyleft — must attribute, derivatives share same license)

### Polygon Counts (Z-Anatomy)
| System | Vertices | Faces |
|--------|----------|-------|
| Skeletal | 300K-500K | 250K-450K |
| Muscular | 800K-1.5M | 700K-1.3M |
| Integumentary | 200K-400K | 150K-350K |
| Organs | 400K-800K | 350K-700K |
| Circulatory | 300K-600K | 250K-500K |
| Nervous | 200K-400K | 150K-350K |
| **Total** | **2.5M-5M** | **2M-4.5M** |

**SOMA Budget:** 200K triangles mobile target → Need LOD reduction (10-25x compression via Meshopt)

## BodyParts3D (Secondary Source)
- FMA (Foundational Model of Anatomy) IDs for every structure — valuable for ontology linking
- 1,500+ distinct structures, male and female templates
- Anatomography web tool for scene composition
- Weakness: OBJ format (no PBR), parts individually modeled (spatial inconsistencies)

## Commercial (Not Available)
- **Complete Anatomy (3D4Medical):** No open-source models, no API, institutional licensing $10K-100K+/yr
- **BioDigital Human:** JS SDK API available (freemium), but models proprietary

## Action Items for SOMA
1. Clone Z-Anatomy repo and set up automated Blender → glTF export pipeline
2. Implement LOD generation (Meshopt decoder) to hit 200K triangle budget
3. Map Blender collection names → SOMA layer system
4. Use BodyParts3D FMA IDs as ontology bridge for SNOMED/LOINC integration

## Sources

- https://github.com/michaelantoniomcnally/Z-Anatomy
- http://lifesciencedb.jp/bp3d
- http://openanatomy.org
