# llm-snomed-ct-automated-mapping-jmir-2026

*Researched: 2026-04-03 13:04 CDT*

# LLM-Assisted SNOMED CT Mapping Tool (JMIR 2026)

**Date:** April 3, 2026
**Source:** JMIR Medical Informatics, Vol 14, 2026 (doi:10.2196/82670)
**Authors:** Park et al. (Kakao Healthcare Corp + Korean university hospitals)

## Summary
A validated LLM-assisted tool that automates SNOMED CT terminology mapping and concept authoring, dramatically reducing manual effort while achieving near-perfect accuracy.

## Key Results
- **Top-5 diagnostic mapping accuracy:** 98.7%, 89.7%, 98.5%, 92.8% across 4 hospital networks (9 hospitals)
- **Top-5 surgical procedural mapping accuracy:** 99.2%, 82.6%, 98.7%, 84.7%
- **Manual mapping reduced by 30%**, overall manual workload reduced by up to **90%**
- **Average mapping + concept creation time reduced by ~75%**
- **Final mapping table processing time reduced by 90%**
- **Duplicate concepts reduced by 83%**, modeling rule violations reduced by **72%**

## How It Works
1. **Preprocess** local institutional terms
2. **Syntactic + LLM vector similarity mapping** (uses GPT-4o for translation + semantic representation)
3. **Iterative enrichment** based on validated results
4. **Post-coordination** for new concept authoring
5. **Machine Readable Concept Model validation** (MRCM)

## Relevance to SOMA
This is the exact solution for our **3D mesh → SNOMED mapping** knowledge gap:

1. **Mesh Label → SNOMED Code:** Use the same LLM-based vector similarity approach to map BodyParts3D/Z-Anatomy mesh labels to SNOMED CT bodySite codes
2. **Bilingual Alignment:** The tool handles translation (Korean→English), so EN→ES alignment is a simpler subset
3. **Post-coordination:** For anatomy concepts not in SNOMED (e.g., specific subdivisions), use structured postcoordination
4. **MRCM Validation:** Ensures our authored concepts follow SNOMED modeling rules

### Proposed Pipeline for SOMA
```
BodyParts3D mesh label → LLM similarity search → SNOMED CT concept ID
                     → SNOMED Spanish Edition → ES label
                     → FHIR BodyStructure resource → bodySite code
                     → 3D model metadata JSON
```

## Future Directions (from paper)
- Leverage SNOMED CT ontology structure + knowledge graphs
- Automated MRCM rule enforcement + inactivation
- Ongoing maintenance + quality assurance

## Sources
- https://medinform.jmir.org/2026/1/e82670
- https://preprints.jmir.org/preprint/82670


## Sources

- https://medinform.jmir.org/2026/1/e82670
