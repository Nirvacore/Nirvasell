# Output 5 — Universal Evidence Matrix

_Auto-generated from `standards_kb/data/`._

*One Evidence · Many Standards.* Each artifact is harvested once and proves multiple controls (and therefore many standards).

| Evidence | Source | Auto? | Proves controls | Indirect standard reach |
|---|---|:-:|---|:-:|
| **EV-POLICY — Approved Policy Document (versioned, signed)** | Document/GRC system | 🤖 | UC-AC, UC-CM, UC-RM, UC-PM, UC-AIG, UC-ESG | 34 |
| **EV-RACI — Roles/RACI & Org Chart with control ownership** | HRIS / GRC | 🤖 | UC-AC, UC-RM, UC-AIG, UC-DG | 20 |
| **EV-RISKREG — Risk Register with assessments & treatments** | GRC / risk tool | 🤖 | UC-RM, UC-SUP, UC-BCM, UC-AIG, UC-VULN | 20 |
| **EV-TRAINLOG — Training completion & awareness records** | LMS | 🤖 | UC-TRN | 8 |
| **EV-ACCESSREVIEW — Periodic access review / recertification logs** | IdP / IAM | 🤖 | UC-AC, UC-LOG | 8 |
| **EV-CHANGETICKET — Change tickets with approvals & rollback** | ITSM / CI-CD | 🤖 | UC-CM, UC-VULN | 10 |
| **EV-INCIDENT — Incident/breach records with timeline & RCA** | ITSM / SIEM | 🤖 | UC-IM, UC-BCM, UC-LOG | 11 |
| **EV-VENDORDD — Vendor due-diligence & contracts (DPA/SLAs)** | Procurement / VRM | 🤖 | UC-SUP, UC-PM | 14 |
| **EV-LOGS — System/audit logs (retained, tamper-evident)** | SIEM / cloud logging | 🤖 | UC-LOG, UC-AC, UC-IM | 12 |
| **EV-SCAN — Vulnerability scan & pen-test reports** | Scanner / pentest | 🤖 | UC-VULN, UC-CRYPTO | 8 |
| **EV-AUDITREPORT — Internal audit reports & management review minutes** | GRC / minutes | 👤 | UC-AUD, UC-FIN | 9 |
| **EV-DSAR — DSAR/consent records & RoPA (Art.30)** | Privacy platform | 🤖 | UC-PM, UC-DG | 11 |
| **EV-MODELCARD — Model card, AI impact assessment & eval results** | ML platform / model registry | 🤖 | UC-AIG | 6 |
| **EV-BCPTEST — BC/DR test & exercise results, RTO/RPO evidence** | BCM tool / DR runbooks | 👤 | UC-BCM | 6 |
| **EV-GHG — GHG inventory & ESG data with assurance trail** | ESG/carbon platform | 🤖 | UC-ENV, UC-ESG | 11 |
| **EV-FINCTRL — ICFR control evidence (reconciliations, approvals)** | ERP / finance | 🤖 | UC-FIN, UC-AUD | 9 |
| **EV-ASSETINV — Asset/CMDB inventory with classification** | CMDB / cloud | 🤖 | UC-AM, UC-DG | 10 |
| **EV-HAZARD — Hazard assessments & safety incident logs** | EHS system | 👤 | UC-OHS | 5 |

**Automation potential:** 15/18 evidence artifacts are machine-harvestable (🤖) directly from source systems — the rest (👤) need human attestation.

## 5.1 Standard → Evidence pack (collect these to cover the standard)

| Standard | Evidence artifacts needed |
|---|---|
| ISO27001 | EV-POLICY, EV-RACI, EV-RISKREG, EV-TRAINLOG, EV-ACCESSREVIEW, EV-CHANGETICKET, EV-INCIDENT, EV-VENDORDD, EV-LOGS, EV-SCAN, EV-AUDITREPORT, EV-DSAR, EV-BCPTEST, EV-FINCTRL, EV-ASSETINV |
| SOC2 | EV-POLICY, EV-RACI, EV-RISKREG, EV-TRAINLOG, EV-ACCESSREVIEW, EV-CHANGETICKET, EV-INCIDENT, EV-VENDORDD, EV-LOGS, EV-SCAN, EV-AUDITREPORT, EV-BCPTEST, EV-FINCTRL, EV-ASSETINV |
| ISO42001 | EV-POLICY, EV-RACI, EV-RISKREG, EV-TRAINLOG, EV-MODELCARD |
| GDPR | EV-POLICY, EV-RACI, EV-TRAINLOG, EV-ACCESSREVIEW, EV-INCIDENT, EV-VENDORDD, EV-LOGS, EV-SCAN, EV-DSAR, EV-ASSETINV |
| ISO9001 | EV-POLICY, EV-RISKREG, EV-TRAINLOG, EV-CHANGETICKET, EV-VENDORDD, EV-AUDITREPORT, EV-FINCTRL |
| ESRS | EV-POLICY, EV-GHG, EV-HAZARD |
