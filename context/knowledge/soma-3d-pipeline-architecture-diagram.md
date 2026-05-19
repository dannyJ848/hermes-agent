# soma-3d-pipeline-architecture-diagram

*Researched: 2026-04-02 22:10 CDT*

# SOMA 3D Anatomy Pipeline — Architecture Diagram

*Generated: 2026-04-02 22:00 CDT*

```
   _____ ____  __  ______         _____ ____      ____  _            ___
  / ___// __ \/  |/  /   |       |__  // __ \    / __ \(_)___  ___  / (_)___  ___
  \__ \/ / / / /|_/ / /| |        /_ </ / / /   / /_/ / / __ \/ _ \/ / / __ \/ _ \
 ___/ / /_/ / /  / / ___ |      ___/ / /_/ /   / ____/ / /_/ /  __/ / / / / /  __/
/____/\____/_/  /_/_/  |_|     /____/_____/   /_/   /_/_ .___/\___/_/_/_/ /_/\___/
                                                       /_/
═════════════════════════════════════════════════════════════════════════════════

                          ┌─────────────────────┐
                          │   DATA SOURCES       │
                          └──────────┬───────────┘
                                     │
              ┌──────────────────────┼───────────────────────┐
              │                      │                       │
    ┌─────────▼─────────┐ ┌─────────▼─────────┐ ┌───────────▼──────────┐
    │  Z-Anatomy GLBs   │ │   FHIR R4 Server   │ │  Patient Health Data │
    │  (CC-BY-SA 4.0)   │ │  (HAPI/Synthea)    │ │  (Observations,      │
    │  11 Systems        │ │                    │ │   Conditions, Labs)   │
    │  2-5M Polys        │ │                    │ │                       │
    └─────────┬──────────┘ └─────────┬──────────┘ └───────────┬──────────┘
              │                      │                        │
              │                      │                        │
   ┌──────────▼──────────┐  ┌───────▼────────┐    ┌──────────▼──────────┐
   │  ZAnatomyLoader.ts  │  │  FhirAdapter.ts │    │ BilingualTerms.ts   │
   │  ├─ LOD Generation  │  │  ├─ Parse R4    │    │  ├─ 45+ EN/ES Terms │
   │  ├─ Meshopt Decode  │  │  ├─ SNOMED Map  │    │  ├─ SNOMED/LOINC    │
   │  └─ Layer Grouping  │  │  └─ BodySite    │    │  └─ patientLabel    │
   └──────────┬──────────┘  └───────┬────────┘    └──────────┬──────────┘
              │                     │                         │
              │      ┌──────────────┼─────────────────────────┘
              │      │              │
              ▼      ▼              ▼
   ╔══════════════════════════════════════════════════════════════════╗
   ║                    THREE.JS  r182+ (WebGPU)                     ║
   ║  ┌────────────────────────────────────────────────────────────┐  ║
   ║  │               WebGPURenderer (auto-fallback → WebGL2)     │  ║
   ║  └────────────────────────────────────────────────────────────┘  ║
   ║                                                                  ║
   ║  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  ║
   ║  │  SSS Material   │  │  Clip/Cross-Sect │  │  Health Overlay│  ║
   ║  │  System (TSL)   │  │  (Stencil Cap)   │  │  (FHIR→Color)  │  ║
   ║  │  ┌────────────┐ │  │  ┌─────────────┐ │  │  ┌───────────┐ │  ║
   ║  │  │ Skin: 2.0  │ │  │  │ 6-plane     │ │  │  │ BNP→Heart │ │  ║
   ║  │  │ Muscle:3.0 │ │  │  │ clip with   │ │  │  │ eGFR→Kidn │ │  ║
   ║  │  │ Organ: 4.0 │ │  │  │ stencil cap │ │  │  │ ALT→Liver │ │  ║
   ║  │  │ Bone: 0.5  │ │  │  │ rendering   │ │  │  │ Hgb→Brain │ │  ║
   ║  │  └────────────┘ │  │  └─────────────┘ │  │  └───────────┘ │  ║
   ║  └─────────────────┘  └──────────────────┘  └────────────────┘  ║
   ║                                                                  ║
   ║  ┌────────────────────────────────────────────────────────────┐  ║
   ║  │               Performance Budget                            │  ║
   ║  │  <200K tris │ <100 draws │ <200MB GPU │ 30 FPS mobile       │  ║
   ║  └────────────────────────────────────────────────────────────┘  ║
   ╚══════════════════════════════════════════════════════════════════╝
                              │
                              ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                       USER INTERFACE                             │
   │                                                                  │
   │  ┌─────────────┐    3D Body Model    ┌──────────────────────┐   │
   │  │ Layer Toggle │ ◄──────────────────► │ Radial Context Menu │   │
   │  │ ├ Skin       │                     │  ├ "Mi Salud"       │   │
   │  │ ├ Muscle     │   SELECT REGION →   │  │  (My Health)      │   │
   │  │ ├ Bone       │   rotating menu     │  └ "Educación"      │   │
   │  │ ├ Organs     │                     │     (Education)     │   │
   │  │ ├ Vessels    │                     └──────────────────────┘   │
   │  │ └ Nerves     │                                               │
   │  └─────────────┘                                               │
   │                                                                  │
   │  ┌────────────────────────────────────────────────────────────┐  │
   │  │  Bilingual Support: EN/ES (auto-detect, i18next)          │  │
   │  │  "Heart" / "Corazón"  │  "Liver" / "Hígado"              │  │
   │  └────────────────────────────────────────────────────────────┘  │
   └──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                    TAURI (Desktop + Mobile)                       │
   │  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
   │  │ SQLite   │  │ Voice     │  │ Camera   │  │ Push          │  │
   │  │ (Local)  │  │ (STT/TTS) │  │ (Future) │  │ Notifications │  │
   │  └──────────┘  └───────────┘  └──────────┘  └───────────────┘  │
   └──────────────────────────────────────────────────────────────────┘

═════════════════════════════════════════════════════════════════════════════════
                           GRACEFUL DEGRADATION
═════════════════════════════════════════════════════════════════════════════════

   WebGPU (Full SSS + Compute)  ──►  WebGL2 (Pre-int SSS)  ──►  Static Images
   Desktop / Modern Mobile            iOS Safari Fallback         Low-end devices

═════════════════════════════════════════════════════════════════════════════════
                          COMPETITIVE ADVANTAGE
═════════════════════════════════════════════════════════════════════════════════

   Feature              Complete Anatomy    BioDigital      SOMA
   ─────────────────    ────────────────    ──────────      ────────────────
   Price                $150/yr             $48/yr          FREE + Open Source
   Bilingual EN/ES      ✗                   ✗               ✓ Built-in
   Patient Health Data  ✗                   ✗               ✓ FHIR Integration
   Open Source Models   ✗                   ✗               ✓ Z-Anatomy
   Target Users         Medical Students    Enterprises     Uninsured Communities
   SSS Rendering        ✓ (Native)          ✗               ✓ (WebGPU TSL)
```

## Component Legend

| Symbol | Meaning |
|--------|---------|
| `┌─▼─┐` | Data flows downward |
| `──►` | One-way dependency |
| `◄──►` | Two-way interaction |
| `╔══╗` | Core rendering engine |
| `║  ║` | Engine subsystems |
| `───` | Data pipeline |


## Sources

- synthesis-soma-3d-anatomy-pipeline-proposal.md
