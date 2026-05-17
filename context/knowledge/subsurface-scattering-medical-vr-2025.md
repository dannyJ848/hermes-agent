# subsurface-scattering-medical-vr-2025

*Researched: 2026-04-11 12:53 CDT*

# Subsurface Scattering for Medical Data in VR (2025)

**Source:** digital-sciences.de/projects/SS25/SS25_07/

## Key Insight
- Without accurately simulating subsurface scattering (SSS), medical imagery risks being inaccurate AND potentially misleading
- SSS is critical for realistic tissue rendering — skin, organs, and soft tissue all exhibit strong subsurface light transport
- Project focuses on VR medical visualization where realism directly impacts diagnostic accuracy

## Relevance to SOMA
- Validates SOMA's investment in SSS shader development (soma-sss-shaders skill)
- Tissue rendering accuracy is not just aesthetic — it's clinically important
- VR applications suggest mobile performance optimization is key constraint
- SSS parameters need to be anatomically accurate per tissue type

## Technical Notes
- SSS in real-time requires approximate models (screen-space, pre-integrated)
- VR doubles the rendering cost (stereo) making efficient SSS critical
- Pre-integrated SSS (Jimenez/Penner) offers good quality/performance tradeoff for mobile

## Sources

- https://digital-sciences.de/projects/SS25/SS25_07/
