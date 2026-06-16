# 04 — Global Standards Research

The full machine-readable registry (78 standards, 63 bodies, 20 controls, 18
evidence types) lives in [`../../standards_kb/`](../../standards_kb/). This
document gives the **founder's view**: for each key standard — purpose, benefit,
core requirements, documents, evidence, audits, and what NIRVA does about it.

> The power move: NIRVA implements **20 universal controls once** and they
> satisfy these standards **many times over** (see
> `standards_kb/docs/04_controls_matrix.md`). You do not build per-standard —
> you build per-control and map.

## ISO management-system family
| Standard | Purpose | Key requirements | Must-have docs | Evidence | Audit | NIRVA product |
|---|---|---|---|---|---|---|
| **ISO 9001** Quality | Consistent quality, customer focus | Context, leadership, risk, process control, improvement | Quality manual, SOPs, records | Process records, CAPA, mgmt review | Internal + cert audit | DOCS, COMPLIANCE |
| **ISO 14001** Environment | Reduce environmental impact | Aspects, obligations, objectives, ops control | EMS policy, aspects register | Monitoring data, audits | Internal + cert | COMPLIANCE |
| **ISO 45001** OH&S | Prevent injury & ill-health | Hazard ID, worker participation, incident mgmt | OH&S policy, risk assessments | Incident logs, training, inspections | Internal + cert | COMPLIANCE, CHECK |
| **ISO 27001** InfoSec | Protect information | Risk-based Annex A controls (93) | ISMS policy, SoA, risk treatment | Access reviews, logs, incidents | Internal + Stage 1/2 | COMPLIANCE, AUDIT |
| **ISO 27701** Privacy | Manage PII (PIMS) | Extends 27001 for privacy roles | RoPA, privacy policy, DPIA | Consent, DSAR records | Internal + cert | COMPLIANCE |
| **ISO 20000** IT Service | Reliable IT services | Service mgmt system, incident/change | Service catalogue, SLAs | Tickets, change records | Internal + cert | (NirvaCore) |
| **ISO 10002 / 10004** | Complaints & satisfaction | Complaints process, CSAT monitoring | Complaints procedure | Complaint logs, CSAT | Internal | COMPLIANCE, DOCS |
| **ISO 22301** BCMS | Survive disruption | BIA, continuity strategies, exercising | BC plans, BIA | Test results, RTO/RPO | Internal + cert | COMPLIANCE, DOCS |
| **ISO 31000** Risk | Manage uncertainty | Principles, framework, process | Risk policy, register | Risk assessments | (guidance) | EXECUTIVE, AUDIT |
| **ISO 55001** Asset | Whole-life asset value | Asset mgmt system | SAMP, asset register | Lifecycle records | Internal + cert | (NirvaCore Fleet) |
| **ISO 37301** Compliance | Manage compliance obligations | Obligations, culture, controls | Compliance policy | Obligation register, monitoring | Internal + cert | COMPLIANCE |

## Manufacturing / lab
| Standard | Purpose | NIRVA |
|---|---|---|
| **IATF 16949** automotive QMS | ISO 9001 + automotive | COMPLIANCE (Future: Manufacturing) |
| **AS9100** aerospace QMS | ISO 9001 + aerospace | COMPLIANCE |
| **ISO 13485** medical-device QMS | Regulatory QMS | COMPLIANCE |
| **ISO 17025** testing/calibration labs | Lab competence & impartiality | COMPLIANCE (Machine Shop metrology) |

## Technology / security
| Standard | Purpose | NIRVA |
|---|---|---|
| **SOC 2** Trust Services | Attest security/availability/confidentiality/privacy | COMPLIANCE, AUDIT |
| **NIST CSF / 800-53** | Cyber risk framework & control catalog | COMPLIANCE |
| **CSA STAR / CCM** | Cloud security assurance | NirvaCloud |
| **OWASP (ASVS/Top10/LLM)** | App & LLM security | NirvaDeploy, NOVA |
| **CIS Controls v8** | Prioritized security safeguards | COMPLIANCE |
| **Secure SDLC (NIST SSDF)** | Secure software practices | NirvaDeploy |

## Privacy
| Standard | Purpose | NIRVA |
|---|---|---|
| **GDPR** | EU personal-data law | COMPLIANCE |
| **PDPA (Thailand)** | Thai personal-data law (฿5M/offence) | COMPLIANCE (localized — key differentiator) |
| **CCPA / CPRA** | California privacy | COMPLIANCE |
| **NIST Privacy Framework** | Privacy risk management | COMPLIANCE |

## ESG / sustainability
| Standard | Purpose | NIRVA |
|---|---|---|
| **GRI** | Impact-materiality disclosure | (NirvaResearch ESG) |
| **SASB / IFRS S1-S2** | Financial-materiality & climate | ESG module |
| **TCFD** | Climate risk disclosure | ESG module |
| **UN SDGs** | 17 global goals alignment | SOUL / group narrative |
| **B Corp** | Verified social/environmental performance | group certification target |

## Why localization is the moat
Global GRC tools (Vanta, Drata, OneTrust) automate **tech** compliance for
**SaaS** companies. None of them do **PDPA + มอก. + Thai labour + physical
workforce** compliance for a **labour-intensive service business**. That gap is
NIRVA's defensible wedge in SEA. See
[06_competitive_landscape.md](06_competitive_landscape.md).
