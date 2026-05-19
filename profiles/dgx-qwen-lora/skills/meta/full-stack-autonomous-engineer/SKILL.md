---
name: full-stack-autonomous-engineer
version: 1.0
created: 2026-04-02
description: Master skill covering every discipline needed to build SOMA end-to-end as a single autonomous engineer. Frontend, backend, mobile, 3D, AI/ML, medical data, DevOps, and security.
tags: [full-stack, autonomous, somA, master, architecture]
---

# Full-Stack Autonomous Engineer for SOMA

## The Complete Skill Map

Every domain SOMA requires, with tool choices and skill references.

### 1. FRONTEND (React + TypeScript)
- **Framework**: React 18+ with TypeScript strict mode
- **3D Engine**: Three.js via React Three Fiber (R3F)
- **Native**: Tauri 2.0 (iOS + Android + Desktop)
- **Styling**: NativeWind (Tailwind for RN) + CSS Modules
- **State**: Zustand (lightweight, no boilerplate)
- **Navigation**: React Navigation (mobile) + React Router (web)
- **Skills**: `anatomy-3d-viewer`, `mobile-3d-anatomy-rendering`, `mobile-css-responsiveness-audit`

### 2. 3D ANATOMY RENDERING
- **Engine**: Three.js r171+ with WebGPU fallback to WebGL 2
- **Loading**: @needle-tools/gltf-progressive (300KB initial + streaming LODs)
- **Compression**: Meshopt (decoder-free) + KTX2 textures
- **Optimization**: gltf-transform CLI for asset pipeline
- **Interaction**: R3F pointer events + react-native-gesture-handler
- **Raycasting**: three-mesh-bvh for fast hit testing
- **Budget**: <100 draw calls, <200K triangles, <200MB GPU memory
- **Skill**: `mobile-3d-anatomy-rendering`

### 3. BACKEND (Rust via Tauri)
- **Database**: SQLite via tauri-plugin-sql
- **Auth**: Biometric (fingerprint/face) via tauri-plugin-biometric
- **Storage**: tauri-plugin-store for settings, Stronghold for sensitive data
- **HTTP**: tauri-plugin-http for API calls
- **File System**: tauri-plugin-fs for asset management
- **Sidecars**: Embed Python/ONNX models for AI inference
- **IPC**: Tauri commands (Rust <-> TypeScript bridge)

### 4. MEDICAL DATA & AI
- **On-device AI**: ExecuTorch (PyTorch models on mobile, sub-20ms)
- **Medical Knowledge**: BioMCP (PubMed, ClinicalTrials.gov, FDA)
- **Speech**: Whisper (bilingual EN/ES STT/TTS)
- **Imaging**: MONAI (DICOM processing, organ segmentation)
- **Drug Data**: OpenFDA, Healthcare MCP
- **Skills**: `whisper-stt-tts`, `monai-medical-imaging`, BioMCP tools

### 5. MEDICAL CONTENT
- **Encyclopedia**: 3-level depth (Patient, Intermediate, Professional)
- **Bilingual**: EN/ES with proper medical terminology
- **Categories**: cardiovascular, respiratory, gastrointestinal, musculoskeletal, renal, dermatologic, neurologic, endocrine, hematologic, sensory
- **Conditions**: Mapped to body regions on 3D model
- **Medications**: Mapped to affected body regions

### 6. OFFLINE-FIRST ARCHITECTURE
```
Device (Offline)                    Cloud (WiFi only)
┌──────────────────┐               ┌──────────────────┐
│ SQLite           │               │ Model updates    │
│ - Health data    │               │ Encyclopedia     │
│ - Medications    │     sync      │ Higher-res 3D    │
│ - Encyclopedia   │◄─────────────►│ Crash reports    │
│ 3D Assets (2MB)  │               │ Analytics        │
│ AI Models (30MB) │               └──────────────────┘
└──────────────────┘
```

### 7. DEVOPS & INFRASTRUCTURE
- **Build**: Tauri CLI (cargo tauri build / cargo tauri android build)
- **CI/CD**: GitHub Actions (lint, test, build per platform)
- **Distribution**: App Store + Google Play + direct download
- **Updates**: tauri-plugin-updater (self-update)
- **Monitoring**: Sentry for crash reporting
- **Tunnel**: Cloudflare tunnel for dev (localhost:1420)
- **Skills**: `build-test-iterate`, `ts-error-batch-fix`

### 8. SECURITY & PRIVACY
- **Data**: All health data stays on-device (SQLite, never cloud)
- **AI**: On-device inference only (no medical data sent to servers)
- **Auth**: Biometric lock, encrypted storage (Stronghold)
- **Network**: Only encyclopedia updates and model downloads over HTTPS
- **Compliance**: HIPAA-conscious design (no PHI leaves device)
- **Audit**: Regular security review of Tauri permissions

### 9. SELF-IMPROVEMENT PIPELINE
- **SAGA Algorithm**: FSRS-based retention + GEPA evolution + Phantom validation
- **Dojo Cron**: Daily 03:00 analysis of errors and session logs
- **Jack of All Trades**: Daily 09:00/21:00 tool discovery scan
- **Skill Sync**: All new skills auto-synced to soma-coder/researcher/tester profiles
- **Knowledge Base**: Qdrant + BM25 hybrid search over all learnings
- **Skill**: `self-adaptive-growth-algorithm`

### 10. SQUAD COORDINATION
- **TeamMCP**: localhost:3100 coordination server
- **Profiles**: soma-coder, soma-researcher, soma-tester
- **Channel**: squad-general for task broadcast
- **Shared Memory**: omem at localhost:8080 (Qdrant-backed)
- **Crons**: Dojo (03:00), X Scanner (09/15/21), Jack of All Trades (09/21)
- **Skill**: `teammcp-setup`, `multi-agent-profiles`

## Technology Decisions Log

| Decision | Choice | Reason | Date |
|----------|--------|--------|------|
| Shell | Tauri 2.0 | Cross-platform, small binary, Rust security | 2026-03 |
| 3D Engine | Three.js + R3F | Largest ecosystem, WebGL/WebGPU, React integration | 2026-03 |
| Compression | Meshopt | No decoder needed, good mobile perf | 2026-04 |
| Progressive | @needle-tools/gltf-progressive | Best mobile loading, density-based LOD | 2026-04 |
| On-device AI | ExecuTorch | PyTorch-native, sub-20ms, RN hooks | 2026-04 |
| State | Zustand | Lightweight, no boilerplate, works RN | 2026-03 |
| Database | SQLite | Offline-first, Tauri native support | 2026-03 |
| Medical API | BioMCP | PubMed/FDA/Trials unified CLI | 2026-04 |
| Coordination | TeamMCP | MCP-native multi-agent, SQLite+SSE | 2026-04 |

## Session Checklist
At start of every session:
1. Check device tier detection implementation
2. Verify 3D model compression pipeline
3. Test touch interaction flow
4. Validate offline-first data sync
5. Profile GPU memory usage
6. Run SAGA skill review cycle
