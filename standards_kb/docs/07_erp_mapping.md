# Output 7 — Universal ERP Mapping

Connects enterprise functional modules to the controls, taxonomy domains and
standards they operationalize. Source: [`../data/erp_mapping.json`](../data/erp_mapping.json).
This is the bridge between *compliance theory* (the graph) and the *operating
business system* (an ERP / the Nirva product family).

## 7.1 Module → standards → controls

| ERP Module | Domains | Key standards | Universal controls |
|---|---|---|---|
| Governance / GRC | L1,L2,L3,L18 | COBIT, ISO 37301, COSO, ISO 38500 | UC-RM, UC-AUD, UC-DOC |
| Human Resources (HCM) | L4,L11,L15 | ISO 30414, ISO 45001, ISO 9001, GDPR | UC-TRN, UC-OHS, UC-AC |
| Finance & Accounting | L5,L3,L18 | COSO, SOX, SOC 1, IFRS | UC-FIN, UC-AUD, UC-AC |
| Procurement / Supply Chain | L9,L2,L20 | ISO 37001, NIST 800-171, DORA, ISO 9001 | UC-SUP, UC-RM, UC-DOC |
| Quality Management | L6,L16,L8 | ISO 9001, IATF 16949, AS9100, ISO 13485 | UC-CM, UC-AUD, UC-DOC |
| EHS | L10,L11,L17 | ISO 14001, ISO 45001, ISO 50001, ESRS | UC-ENV, UC-OHS |
| IT Service Management | L6,L12,L16 | ISO 20000, ITIL, COBIT | UC-CM, UC-IM, UC-AM |
| Information Security / Cyber | L12,L19 | ISO 27001, NIST 800-53, SOC 2, PCI DSS, CIS, NIS2 | UC-AC, UC-LOG, UC-CRYPTO, UC-VULN, UC-IM, UC-BCM |
| Data Privacy | L13,L20 | ISO 27701, GDPR, PDPA TH/SG, CCPA, HIPAA | UC-PM, UC-DG |
| AI / Model Governance | L14,L2 | ISO 42001, NIST AI RMF, EU AI Act, OECD AI, OWASP LLM | UC-AIG, UC-RM |
| Risk Management | L2,L1 | ISO 31000, COSO ERM, NIST CSF | UC-RM, UC-BCM |
| Business Continuity | L19,L6 | ISO 22301, DORA, NIST CSF | UC-BCM, UC-IM |
| ESG / Sustainability | L17,L10,L1 | ESRS, GRI, IFRS S1/S2, GHG Protocol, CSRD, TNFD | UC-ESG, UC-ENV |
| Asset Management (EAM) | L7,L6 | ISO 55001, ISO 27001 | UC-AM |
| Customer / CRM | L8,L13 | ISO 9001, WCAG, GDPR | UC-PM |
| Audit & Assurance | L18,L3 | ISO 19011, SOC 2, SOX | UC-AUD |

## 7.2 Canonical data objects per module

The compliance engine reads/writes these business objects; each is the carrier
for evidence and control state.

| Module | Data objects |
|---|---|
| GRC | policy, risk, control, audit, obligation |
| HCM | employee, competency, training, role, incident |
| Finance | ledger, reconciliation, approval, journal |
| Procurement | vendor, contract, DPA, assessment, PO |
| Quality | process, nonconformity, CAPA, inspection |
| EHS | hazard, aspect, permit, emission, incident |
| ITSM | service, ticket, CI, change, SLA |
| InfoSec | asset, vulnerability, log, incident, key |
| Privacy | RoPA, consent, DSAR, DPIA, data-subject |
| AI Gov | model, dataset, AIA, eval, deployment |
| BCM | BIA, plan, test, RTO, RPO |
| ESG | metric, disclosure, target, emission-factor, materiality |

## 7.3 Why this matters for NirvaSell (the current app)

The existing `nirva.sell` app already contains the seeds: `compliance.py`
(pre-flight marketplace rule checks), `legal.py`, `policy_watcher.py`,
`E_📋_Policies.py`, `O_🛡_Compliance.py`. Those map cleanly onto the
**Customer/CRM**, **Data Privacy** and **GRC** modules above. The universal
model lets a reseller-grade SKU compliance check and an enterprise ISO 27001
program share the same control/evidence backbone — only the *mappings* differ.

## 7.4 Integration pattern
Each ERP module exposes its data objects to the **evidence harvester** (push or
pull). The harvester normalizes them into `EV-*` artifacts, which the mapping
engine attaches to `UC-*` controls. No module needs to know which standards it
is helping satisfy — that knowledge lives entirely in the graph.
