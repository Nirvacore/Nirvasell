# 03 — Problem Atlas: The Fears Executives Pay To Remove

Source: [`../data/problems.json`](../data/problems.json) (full root-cause,
impact, early-warning, prevention and NIRVA mapping for each). This is the
demand-side case — NIRVA sells *removal of fear*, not features.

## The 16 fears, ranked by how fast they create urgency

### Tier A — money walking out the door (sell first)
| Fear | One-line root cause | NIRVA | Standards reach |
|---|---|---|:-:|
| **Ghost Employee** | No tamper-proof link between paid headcount and a verified human | CHECK, AUDIT | 13 |
| **Payroll Fraud** | Payroll computed from un-auditable inputs; preparer = approver | CHECK, AUDIT | 15 |
| **Fake Attendance** | Shared logins, photo-of-photo, GPS spoofing on LINE | CHECK | 8 |
| **Procurement Fraud** | Opaque approvals, no vendor due diligence, PO splitting | PROCURE, AUDIT | 13 |

### Tier B — existential / legal (sell on risk)
| Fear | Root cause | NIRVA | Reach |
|---|---|---|:-:|
| **Compliance Failure** | Evidence scattered; controls unmonitored; surprise at audit | COMPLIANCE, AUDIT, DIAGNOSIS | 19 |
| **Data Breach** | PII in unsecured Excel/LINE; no access control/RoPA/consent | COMPLIANCE | 20 |
| **Safety Incident** | Hazards uncontrolled; no near-miss reporting; training gaps | COMPLIANCE, CHECK | 17 |
| **Contract Risk** | Contract terms not linked to operational reality | CHECK, PROCURE, COMPLIANCE | 13 |

### Tier C — slow bleed / fragility (sell on resilience)
| Fear | Root cause | NIRVA | Reach |
|---|---|---|:-:|
| **Operational Blind Spot** | Fragmented data; backward-looking reports | EXECUTIVE, DIAGNOSIS | 14 |
| **Knowledge Loss** | Know-how lives in heads & private chats | DOCS, WISDOM, LIFE | 10 |
| **High Turnover** | Low dignity/recognition, surveillance culture | LIFE, WISDOM, DIAGNOSIS | 8 |
| **Customer Complaint Spiral** | Complaints not captured/resolved systematically | COMPLIANCE, LIFE | 9–17 |
| **Poor Documentation** | Uncontrolled docs, no retention, evidence gaps | DOCS, AUDIT | 9 |
| **Workforce Shortage / No-Show** | No real-time required-vs-actual visibility | CHECK, EXECUTIVE | 7 |
| **Leadership / Key-Person Dependency** | Decisions & relationships concentrated in few heads | EXECUTIVE, DOCS, WISDOM | 13 |
| **Single Point of Failure** | No redundancy, no continuity plan, undocumented criticals | EXECUTIVE, DOCS, COMPLIANCE | 13 |

## How each problem is analyzed (the data model)
Every entry carries:
- **root_cause** — why it actually happens (not the symptom)
- **impact** — financial / legal / reputation, quantified where possible
- **early_warning** — the signals NIRVA watches for
- **prevention** + **best_practice** — the world-class fix
- **nirva / controls / standards** — the exact mapping into the platform & graph

## The reframe that wins the sale
Most of these fears share **one** root cause: *reality is captured in
un-verifiable, fragmented form (LINE/Excel/PDF), so nobody can trust the
numbers.* NIRVA fixes the root cause once (LY1+LY2) and the whole tier of fears
recedes together. That's why NIRVA is an OS, not a point tool — you don't buy 16
apps, you remove one root cause.

## The dignity guardrail
Note that the *same* check-in data that exposes ghost employees also proves an
honest worker was present and safe, lets them get paid correctly and on time,
and protects them in a dispute. NIRVA frames every "fraud" feature as a
"fairness" feature — that is how you deploy it to 1,356 people without fear.
