# Output 6 — Universal Compliance Architecture

The architecture that turns the knowledge graph into a running **Nirva Universal
Compliance Engine** across the Nirva product family.

## 6.1 Design principle

> **One Data · One Evidence · Many Standards.**

A control is implemented once. An evidence artifact is collected once. The
mapping layer (this knowledge graph) fans that single effort out to every
standard, regulation and framework that requires it. Adding a new standard
becomes a *mapping exercise*, not a re-implementation.

## 6.2 Layered architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  EXPERIENCE     NirvaSell · NirvaTrade · partner & customer portals │
│                 Compliance dashboards · audit-room · attestations   │
├──────────────────────────────────────────────────────────────────┤
│  INTELLIGENCE   Nirva Universal Compliance Engine                   │
│   • Standards Knowledge Graph  (this package)                       │
│   • Crosswalk / mapping engine  (Control→Standard, Evidence→Control)│
│   • Gap & conflict analyzer     (Phase 5 register)                  │
│   • Continuous control monitoring + AI copilots                     │
├──────────────────────────────────────────────────────────────────┤
│  CONTROL        NirvaCore — unified control & evidence data model    │
│   • 20 universal controls   • 18 evidence types   • RoPA/risk reg.  │
├──────────────────────────────────────────────────────────────────┤
│  PLATFORM       NirvaOS (tenancy, identity, policy-as-code)         │
│                 NirvaCloud (regional data planes)                   │
│                 NirvaDeploy (CI/CD with compliance gates)           │
├──────────────────────────────────────────────────────────────────┤
│  SOURCES        ERP · HRIS · IdP · SIEM · ITSM · ML registry ·      │
│                 cloud · ESG/carbon · finance — evidence harvesters  │
└──────────────────────────────────────────────────────────────────┘
```

## 6.3 Role of each Nirva component

| Component | Responsibility in the compliance engine |
|---|---|
| **NirvaCore** | System-of-record for controls, evidence, risks, obligations. Hosts the knowledge graph and the `edges` store. |
| **NirvaOS** | Multi-tenant runtime: identity, RBAC, **policy-as-code**, workflow, audit log. Enforces controls at execution time. |
| **NirvaCloud** | Regional data planes resolving the data-localization conflict (`CON-LOCALIZATION-GLOBAL`): data stays in-region, metadata graph is global. |
| **NirvaDeploy** | CI/CD with **compliance gates** — policy checks in the pipeline resolve `CON-COMPLIANCE-INNOVATION`. |
| **NirvaSell** | Commercial surface: packages compliance as products/modules for resellers and SMEs (the existing nirva.sell app is the seed). |
| **NirvaTrade** | Cross-org trust exchange: share attestations/SOC reports with partners under controlled disclosure. |

## 6.4 Data flow — "collect once, certify many"

```
 1. Source system event (e.g. IdP access review completes)
        ↓  harvester (auto_collectable=true)
 2. Evidence artifact stored in NirvaCore  (EV-ACCESSREVIEW)
        ↓  Evidence —PROVES→ Control
 3. Control state updated                  (UC-AC = effective)
        ↓  Control —SATISFIES→ Standards
 4. Compliance posture recomputed for ISO 27001, SOC 2, PCI DSS, GDPR, …
        ↓  Standard —COVERS→ Domain
 5. Domain dashboards (Security, Privacy, People) refresh in real time
```

## 6.5 Reference services

| Service | Function |
|---|---|
| **Mapping engine** | Resolves Control↔Requirement↔Standard crosswalks (controls.json). |
| **Evidence harvester** | Pulls artifacts from sources; 15/18 types are machine-collectable. |
| **Continuous Control Monitoring (CCM)** | Re-evaluates control effectiveness on a schedule/trigger. |
| **Gap analyzer** | For a target standard, returns missing controls + missing evidence. |
| **Conflict analyzer** | Surfaces Phase-5 tensions active for the tenant's chosen standards and recommends the documented resolution. |
| **AI compliance copilot** | Drafts policies, suggests control mappings, summarizes audit gaps — itself governed by `UC-AIG` (eat-your-own-governance). |

## 6.6 Multi-tenancy & data residency
- **Global control plane**: the knowledge graph, mappings, taxonomy (no personal data).
- **Regional data planes**: tenant evidence and personal data pinned to a region (NirvaCloud), reconciling EU/Thai/Singapore/China residency rules.
- **Tenant isolation**: per-tenant control state and evidence stores, mirroring the existing nirva.sell SQLite-per-user pattern at enterprise scale.

## 6.7 Non-functional guardrails
Immutable, tamper-evident audit log (`UC-LOG`) · evidence retention schedule
reconciling `CON-RETENTION-RTBF` · cryptographic protection of evidence
(`UC-CRYPTO`) · least-privilege access to the compliance data itself (`UC-AC`).
