# Output 10 — Future Standards Roadmap

The knowledge graph is a living asset. This roadmap tracks the standards
pipeline and the platform capabilities needed to absorb them — so the Nirva
engine stays current without re-architecture.

## 10.1 Emerging & in-flight standards to add

| Standard / regulation | Body | Status | Domain | Why it matters |
|---|---|---|---|---|
| ISO/IEC 42005 (AI system impact assessment) | ISO/IEC | Published 2025 | L14 | Operational AIA method for `UC-AIG` |
| ISO/IEC TS 42119 / 42006 (AI audit & body reqs) | ISO/IEC | Developing | L14,L18 | Certifying AIMS auditors |
| ISO/IEC 27090 / 27091 (AI security & privacy) | ISO/IEC | Developing | L12,L13,L14 | Securing AI systems |
| EU AI Act — GPAI Codes of Practice | EU | Phasing in 2025–2027 | L14,L20 | General-purpose & foundation models |
| US state privacy laws (TX, OR, CO, …) | US states | Rolling | L13 | Multi-state DSAR fragmentation |
| ISO 27001 transition completion | ISO/IEC | 2022→ (deadline 2025) | L12 | Annex A re-mapping (114→93 controls) |
| TNFD adoption / nature disclosures | TNFD | Scaling | L17,L10 | Nature alongside climate |
| ISSB jurisdictional adoptions | national regulators | Rolling | L17 | IFRS S1/S2 becoming mandatory locally |
| Quantum-safe / PQC migration (NIST FIPS 203–205) | NIST | Published 2024 | L12 | Crypto-agility for `UC-CRYPTO` |
| DORA technical standards (RTS/ITS) | EU/ESAs | In force 2025 | L19,L9 | Financial-sector resilience detail |
| Cyber Resilience Act (CRA) | EU | Applies 2027 | L12,L9 | Product security obligations |
| ISO 27701:2025 (standalone PIMS revision) | ISO/IEC | Revising | L13 | Decoupling PIMS from ISO 27001 |

## 10.2 Platform capability roadmap

| Horizon | Capability | Outcome |
|---|---|---|
| **Now (v1)** | Static graph + validator + crosswalk docs (this package) | Authoritative map; manual mapping |
| **Near** | Evidence harvester connectors (IdP, SIEM, ITSM, ESG) | 15/18 evidence types auto-collected |
| **Near** | Continuous Control Monitoring (CCM) jobs | Control state recomputed on schedule/trigger |
| **Mid** | AI mapping copilot (suggest Control↔Standard links) | New standards mapped in hours, governed by `UC-AIG` |
| **Mid** | Regulatory change feed → graph diffs | Auto-flag impacted controls when a standard updates (extends existing `policy_watcher.py`) |
| **Mid** | Graph DB backend (Neo4j) + SHACL validation | Reasoning, gap inference at scale |
| **Far** | Cross-org trust exchange (NirvaTrade) | Share attestations under controlled disclosure |
| **Far** | Predictive compliance (forecast gaps before audits) | Risk-led, proactive posture |

## 10.3 Graph growth targets

| Dimension | v1 (now) | Target |
|---|---|---|
| Organizations | 61 | 100+ (add national NSBs, sector bodies) |
| Standards | 73 | 500+ (sector & national depth) |
| Universal controls | 20 | 60–80 (finer granularity) |
| Evidence types | 18 | 50+ (richer auto-harvest) |
| ERP modules | 16 | full enterprise coverage |
| Clause-level mappings | family-level | clause/control granular crosswalks |

## 10.4 Governance of the graph itself
- **Versioning:** every data file carries `schema_version`; tag releases.
- **Validation gate:** `python -m standards_kb.graph` must pass in CI before
  merge (see suggested SessionStart hook / pre-commit).
- **Provenance:** add `source` + `last_reviewed` per node as the graph scales,
  so each mapping is auditable — the compliance engine must itself be auditable.
- **Licensing discipline:** keep mappings (our IP) separate from copyrighted
  standard text (referenced, never reproduced).

## 10.5 The north star

> **"The Universal Operating System for Compliance"** — where any organization
> declares the standards it must meet, connects its source systems once, and the
> Nirva engine continuously proves conformance across all of them from a single
> body of data and evidence.
>
> One Data · One Evidence · Many Standards.
