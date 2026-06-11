# Output 1 — Complete Standards Registry

The registry is the canonical list of **who makes standards** (Phase 1) and
**what the standards are** (Phase 2). The machine-readable source of truth is
[`../data/organizations.json`](../data/organizations.json) and
[`../data/standards.json`](../data/standards.json). This document is the human
index.

## 1.1 Standards organizations (Phase 1)

61 bodies catalogued, grouped by scope.

### Global (international)
ISO · IEC · ITU · OIML · BIPM · ISO/IEC JTC 1

### Technology / ICT consortia
IEEE · IETF · W3C · OASIS · 3GPP · Cloud Security Alliance (CSA) · PCI SSC

### United States
ANSI · NIST · ASTM · ASME · NFPA · SAE · API · AICPA · COSO · PCAOB · FASB

### Europe (regional)
CEN · CENELEC · ETSI · ENISA · EDPB · EFRAG · European Commission

### National standards bodies
BSI (UK) · DIN (DE) · AFNOR (FR) · JISC (JP) · SAC (CN) · KATS (KR) ·
**TISI (TH)** · SCC (CA) · Standards Australia · BIS (IN) · ABNT (BR) ·
Enterprise Singapore

### Frameworks, good-practice & regulators
ISACA (COBIT) · AXELOS (ITIL) · GRI · SASB · ISSB · IFRS Foundation ·
GHG Protocol · TCFD · TNFD · CDP · SBTi · UN Global Compact · OECD · OWASP ·
CIS · MITRE · PMI · Thailand PDPC

> The registry deliberately mixes **formal SDOs** (ISO, IEC, IEEE…),
> **frameworks bodies** (ISACA, COSO, AICPA…) and **regulators**
> (European Commission, PDPC…). For a universal compliance engine they all
> produce *obligations*, so they share one node type.

## 1.2 Standards catalogue (Phase 2)

73 standards captured with: name · code · first year · latest version · status ·
type · industries · scope · website · taxonomy domains. Highlights by family:

### Management systems (Annex SL / Harmonized Structure)
| Code | Title | Domain focus |
|---|---|---|
| ISO 9001:2015 | Quality | Operation, Customer, Improvement |
| ISO 14001:2015 | Environment | Environment, Sustainability |
| ISO 45001:2018 | Occupational H&S | Safety, People |
| ISO 22301:2019 | Business Continuity | Continuity, Risk |
| ISO/IEC 27001:2022 | Information Security | Security, Privacy |
| ISO/IEC 27701:2019 | Privacy (PIMS) | Privacy |
| ISO/IEC 42001:2023 | AI Management | AI, Governance |
| ISO 55001:2024 | Asset Management | Asset |
| ISO/IEC 20000-1:2018 | IT Service Mgmt | Operation |
| ISO 37301:2021 | Compliance Mgmt | Compliance, Legal |
| ISO 50001:2018 | Energy | Environment |
| ISO 30401:2018 | Knowledge Mgmt | Knowledge |

### Risk & governance frameworks
ISO 31000 · IEC 31010 · COSO IC-IF · COSO ERM · COBIT 2019 · ITIL 4 · ISO 38500

### Security & cyber
NIST CSF 2.0 · NIST SP 800-53 r5 · SP 800-171 · CIS Controls v8.1 · CSA CCM v4 ·
PCI DSS v4.0.1 · OWASP ASVS · OWASP LLM Top 10 · MITRE ATT&CK · MITRE ATLAS ·
TLS 1.3 · OAuth 2.0

### Attestation & audit
SOC 1 · SOC 2 · SOC 3 · ISO 19011

### Privacy & data law
GDPR · PDPA (Thailand) · PDPA (Singapore) · CCPA/CPRA · HIPAA · NIST Privacy
Framework

### AI governance
ISO/IEC 42001 · ISO/IEC 23894 · ISO/IEC TR 24028 · NIST AI RMF · EU AI Act ·
OECD AI Principles · OWASP LLM Top 10 · MITRE ATLAS

### ESG & sustainability
ESRS / CSRD · GRI Standards · SASB · IFRS S1 · IFRS S2 · GHG Protocol · TCFD ·
TNFD · ISO 26000 · ISO 30414

### Sector quality systems
ISO 13485 (medical) · ISO 22000 (food) · IATF 16949 (automotive) ·
AS9100 (aerospace)

### Regulations (EU digital & resilience)
EU AI Act · NIS2 · DORA · CSRD · GDPR · SOX

## 1.3 Status legend
`active` · `revised` (superseded/transitioning) · `withdrawn` · `draft` ·
`emerging`. See [10_future_roadmap.md](10_future_roadmap.md) for the emerging
pipeline.

## 1.4 How to extend
Add a node to the relevant JSON file using the documented `fields`, then run
`python -m standards_kb.graph` — the validator will reject any dangling
reference before the change lands.
