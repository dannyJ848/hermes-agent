# healthcare-mcp-servers-soma-2026

*Researched: 2026-04-07 12:12 CDT*

# Healthcare MCP Servers for SOMA (April 2026)

Source: GitHub, Momentum AI, MintMCP

## Key Servers Found

### 1. WSO2 FHIR MCP Server (github.com/wso2/fhir-mcp-server)
- Expose ANY FHIR server/API as an MCP server
- Designed for developers and integrators
- Enterprise-grade (WSO2 is a major integration platform vendor)

### 2. Momentum FHIR MCP Server (themomentum.ai)
- Natural language queries to FHIR healthcare data
- Automatic LOINC and SNOMED code resolution
- Query patient records, lab results, medications with plain language

### 3. Momentum Apple Health MCP Server
- Apple Health data queryable by AI agents
- Bridge for health data → analytics tools

### 4. MCP Gateways for Healthcare (MintMCP)
- SOC 2 compliance, PHI protection
- Seamless EHR integration
- Secure AI deployments in healthcare settings

## SOMA Integration Path
1. **FHIR MCP Server** → Connect SOMA to real patient data (FHIR APIs)
2. **LOINC/SNOMED resolution** → Bilingual medical terms can auto-map to standard codes
3. **Apple Health MCP** → Could feed real patient vitals into SOMA's anatomy context
4. **Secure gateway** → Required for any clinical deployment of SOMA

## Action Items
- Test WSO2 FHIR MCP Server with Hermes native MCP client
- Evaluate LOINC/SNOMED auto-resolution for SOMA bilingual terminology
- Monitor MintMCP gateway for HIPAA-compliant deployment patterns


## Sources

- https://github.com/wso2/fhir-mcp-server
- https://www.themomentum.ai/open-source/fhir-mcp-server
- https://www.mintmcp.com/blog/gateways-healthcare-organizations-with-mcp
