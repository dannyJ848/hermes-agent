# DGX-MacBook Infrastructure Access Pattern

*Researched: 2026-05-16 11:17 CDT*

## Critical Infrastructure Mapping

**DGX Spark Server**
- Hostname: `spark-85e8.local`
- Access from MacBook: `ssh djg6228@spark-85e8.local`
- Auth: NVIDIA Sync config + nvsync.key (NOT id_ed25519)
- Hermes path: `/data/SpecForge/hermes-agent`
- vLLM: Docker container on port 8000

**MacBook Air**
- Hostname: `MacBook-Air-9.local`
- Access from DGX: `ssh macbook` (configured in DGX ~/.ssh/config)
- Auth: Standard id_ed25519 key
- Hermes path: `~/hermes-agent`

**Key Rule**: Never guess IPs. Always use hostnames. After DGX restart, clear known_hosts with `ssh-keygen -R spark-85e8.local` and reconnect with `-o StrictHostKeyChecking=accept-new`.

**Failure Mode**: Confusing the two systems' IPs or auth methods results in immediate connection loss to DGX, cutting off the terminal bridge.
