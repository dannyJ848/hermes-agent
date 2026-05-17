# soma-fhir-server-ecosystem

*Researched: 2026-04-02 16:24 CDT*

# FHIR R4 Servers for SOMA

## Top Recommendations for SOMA (Mobile, Open Source, Patient-Facing)

### Medplum (BEST FIT)
- URL: https://github.com/medplum/medplum
- License: Apache 2.0
- Stack: TypeScript/Node.js + PostgreSQL + Redis
- SMART on FHIR: Built-in
- $export: Full support
- Docker: docker-compose available
- **Why: TypeScript SDK matches SOMA's stack. React component library included. Hosted free tier.**

### HAPI FHIR (Most Battle-Tested)
- URL: https://github.com/hapifhir/hapi-fhir
- License: Apache 2.0
- Stack: Java/Spring Boot + PostgreSQL
- SMART on FHIR: Yes (needs Keycloak)
- $export: Full support
- Docker: `hapiproject/hapi:latest` (one-command start)
- **Why: Most feature-complete, widest production adoption**

### Smile CDR (Enterprise, Free Trial)
- URL: https://smilecdr.com
- SMART on FHIR: Built-in OIDC (best turnkey)
- Free trial Docker available

## EHR FHIR APIs (Patient Connection)
| EHR | Auth | Patient Access |
|-----|------|---------------|
| Epic MyChart | SMART on FHIR | Yes |
| Oracle Health (Cerner) | SMART on FHIR | Yes |
| athenahealth | OAuth2 | Yes |
| eClinicalWorks | OAuth2 | Yes |

## Key Registries
- SMART App Launcher: https://launch.smarthealthit.org
- Epic Dev Portal: https://fhir.epic.com
- 1upHealth (aggregator): https://1up.health (700+ EHRs)

## Latin American FHIR
- HL7 Chile: https://www.hl7chile.cl (active FHIR IGs)
- HL7 Argentina: https://www.hl7arg.org.ar (FHIR IGs in progress)
- HL7 Spain: https://hl7spain.org (FHIR ES profiles)

## SOMA Integration Plan
1. Dev: Medplum (TypeScript-native, matches app stack)
2. Testing: SMART Health IT sandbox
3. Production: Medplum self-hosted or HAPI FHIR + Keycloak
4. Patient data: Epic/Cerner SMART on FHIR for US, HL7 Chile/Argentina for LATAM


## Sources

- https://github.com/medplum/medplum
- https://github.com/hapifhir/hapi-fhir
- https://launch.smarthealthit.org
- https://fhir.epic.com
