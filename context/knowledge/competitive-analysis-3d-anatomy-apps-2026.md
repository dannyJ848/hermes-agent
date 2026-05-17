# competitive-analysis-3d-anatomy-apps-2026

*Researched: 2026-04-02 19:56 CDT*

# Competitive Analysis: 3D Anatomy Apps (April 2026)

## Complete Anatomy (3D4Medical / Elsevier)
- **Pricing**: $39.99/yr (student, first year), $99.99/yr (professional)
- **Platforms**: iOS, macOS, Windows, Android
- **Key Features**:
  - Full male + female 3D gross anatomy models
  - Cross-sections (transverse view)
  - Cut, dissect, and annotate tools
  - Interactive radiology images (95 CT, 16 MRI, 11 angiography, 10 radiograph, 8 mammogram)
  - 20+ microanatomy models, 2 cell biology models
  - Course library (undergraduate, clinical, specialty)
  - Courses in English only; some video subtitles in EN/ES/ZH/FR/DE
  - Curriculum manager for institutions
- **Weaknesses for our target users**:
  - Paid ($40-100/yr is expensive for uninsured/low-income users)
  - Courses NOT in Spanish (only some subtitles)
  - No FHIR/health data integration
  - No personalized health data visualization

## BioDigital Human
- **Pricing**: Free basic, $12/yr premium
- **Platforms**: Web, iOS, Android
- **Features**: 3D models, cross-sections, x-ray mode, bookmarks
- **Weakness**: Limited free content, English-only, no personal health data

## Visible Body (Human Anatomy Atlas)
- **Pricing**: $24.99 one-time (student)
- **Platforms**: iOS, Android, Web, PC/Mac
- **Features**: 3D models, cross-sections, muscle actions, animations
- **Weakness**: English-only, no health data integration, limited bilingual

## Primal Pictures
- **Pricing**: Institutional licensing ($$$$)
- **Focus**: Professional medical education, surgical planning
- **Weakness**: Not accessible to individuals, no Spanish, not mobile-first

## SOMA's Competitive Advantages
1. **Free and open-source** — removes financial barrier for low-income communities
2. **Fully bilingual EN/ES** — not just subtitles, but complete Spanish UI and terminology
3. **Personal health data integration** — FHIR R4 adapter maps conditions/medications to 3D body
4. **Community-focused** — designed for Spanish-speaking uninsured populations
5. **AI-powered** — LLM tutor in Spanish for anatomy education

## 5 Actionable Recommendations for SOMA
1. **Match Complete Anatomy's cross-section feature** — we now have AnatomyCrossSection.tsx with axial/sagittal/coronal planes ✓
2. **Add microanatomy/histology viewer** — Complete Anatomy has 20+ micro models; SOMA needs histology slides linked to 3D regions
3. **Interactive radiology overlay** — ability to import and overlay patient CT/MRI on the 3D model (FHIR ImagingStudy resources)
4. **Spanish course content** — create anatomy courses entirely in Spanish, not just translated subtitles
5. **Dissection recording** — let users save and share dissection sequences as educational content


## Sources

- https://store.3d4medical.com/
- https://www.visiblebody.com/blog/how-does-visible-body-courseware-compare-to-3d4medicals-complete-anatomy
