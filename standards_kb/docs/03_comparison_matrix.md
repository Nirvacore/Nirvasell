# Output 3 — Standards Comparison Matrix

_Auto-generated from `standards_kb/data/`. Do not edit by hand — run `python -m standards_kb.build_reports`._

## 3.1 Common-DNA × Framework coverage

Rows = shared requirement primitives (Phase 4). A ✅ means the framework explicitly carries that requirement. The density of this matrix is the mathematical basis for *write-once-certify-many*.

| Requirement (HS clause) | ISO9001 | ISO27001 | ISO42001 | SOC2 | COBIT | ITIL | NISTCSF | GDPR | ESRS | Σ |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Policy** (5.2) | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | 14 |
| **Roles, Responsibilities & Authorities** (5.3) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | 13 |
| **Context & Interested Parties** (4.1-4.2) | ✅ | ✅ | ✅ | — | — | — | — | — | — | 8 |
| **Risk Assessment** (6.1) | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | 16 |
| **Objectives & Planning** (6.2) | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — | 8 |
| **Competence** (7.2) | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | 10 |
| **Awareness & Training** (7.3) | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | 11 |
| **Communication** (7.4) | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | — | 8 |
| **Documented Information** (7.5) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | 12 |
| **Operational Planning & Control** (8.1) | ✅ | ✅ | ✅ | — | — | ✅ | — | — | — | 8 |
| **Monitoring, Measurement & KPI** (9.1) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | 12 |
| **Evidence / Records of Conformity** (9.1/7.5) | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | 10 |
| **Internal Audit** (9.2) | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — | 10 |
| **Management Review** (9.3) | ✅ | ✅ | ✅ | — | — | — | — | — | — | 8 |
| **Nonconformity & Corrective Action** (10.2) | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | 9 |
| **Continual Improvement** (10.1/10.3) | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | 9 |
| **Incident / Event Management** (8.x) | — | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | — | 12 |
| **Third-Party Due Diligence** (8.x) | — | ✅ | — | ✅ | — | — | — | ✅ | — | 8 |
| **Impact Assessment (DPIA/AIA)** (6.1.x) | — | — | ✅ | — | — | — | — | ✅ | — | 6 |

## 3.2 Cross-standard similarity (semantic overlap of expression)

| Requirement | Similarity | Appears in N standards |
|---|:-:|:-:|
| Context & Interested Parties | 0.95 | 8 |
| Documented Information | 0.94 | 12 |
| Competence | 0.93 | 10 |
| Management Review | 0.93 | 8 |
| Policy | 0.92 | 14 |
| Objectives & Planning | 0.91 | 8 |
| Nonconformity & Corrective Action | 0.91 | 9 |
| Roles, Responsibilities & Authorities | 0.90 | 13 |
| Internal Audit | 0.90 | 10 |
| Continual Improvement | 0.89 | 9 |
| Awareness & Training | 0.88 | 11 |
| Communication | 0.86 | 8 |
| Risk Assessment | 0.85 | 16 |
| Monitoring, Measurement & KPI | 0.84 | 12 |
| Evidence / Records of Conformity | 0.82 | 10 |
| Operational Planning & Control | 0.80 | 8 |
| Incident / Event Management | 0.78 | 12 |
| Third-Party Due Diligence | 0.76 | 8 |
| Impact Assessment (DPIA/AIA) | 0.72 | 6 |

> **Reading:** requirements above ~0.85 (Context, Documented Information, Competence, Management Review, Policy) are near-identical across ISO management systems — implement the control once and reuse the evidence for every certification.
