# Output 9 — ESG Mapping

How the graph harmonizes the fragmented ESG/sustainability reporting landscape
onto two controls (`UC-ESG`, `UC-ENV`) and a reusable disclosure data set.

## 9.1 The ESG standards landscape (Domain L17)

| Standard | Body | Lens | Status |
|---|---|---|---|
| **ESRS** (under CSRD) | EFRAG/EU | Double materiality, mandatory in EU | Binding (phased from FY2024) |
| **GRI Standards** | GRI | Impact materiality (outward) | Voluntary, widely adopted |
| **IFRS S1** | ISSB | Sustainability financial materiality | Global baseline |
| **IFRS S2** | ISSB | Climate (absorbs TCFD) | Global baseline |
| **SASB** | ISSB-maintained | Industry-specific financial materiality | Feeds IFRS S1 |
| **GHG Protocol** | WRI/WBCSD | Carbon accounting (Scope 1/2/3) | De-facto global |
| **TCFD** | FSB | Climate risk (4 pillars) | Folded into ISSB (2024) |
| **TNFD** | TNFD | Nature/biodiversity (LEAP) | Emerging voluntary |
| **ISO 26000** | ISO | Social responsibility guidance | Non-certifiable |
| **ISO 14001 / 50001** | ISO | Environmental/energy mgmt systems | Certifiable, operational |

## 9.2 Materiality reconciliation

The central ESG tension is *which* materiality:

| Lens | Standards | Question answered |
|---|---|---|
| **Impact materiality** | GRI, ESRS (inward+outward) | How does the company affect people & planet? |
| **Financial materiality** | IFRS S1/S2, SASB | How do sustainability issues affect enterprise value? |
| **Double materiality** | **ESRS** | Both, simultaneously (EU legal requirement) |

> Engine strategy: capture data once at the **double-materiality** superset
> (ESRS), then *project down* to GRI (impact subset) and IFRS S1/S2 (financial
> subset). One data set, many disclosures — the ESG instance of the platform
> principle.

## 9.3 Crosswalk — ESRS topical standards → controls/domains

| ESRS | Topic | Domain | Control | Reuses |
|---|---|---|---|---|
| ESRS 2 | General disclosures | L1 | UC-ESG | Governance from COSO/ISO 38500 |
| ESRS E1 | Climate change | L10 | UC-ENV | GHG Protocol, IFRS S2 |
| ESRS E2–E5 | Pollution, water, biodiversity, circular economy | L10 | UC-ENV | ISO 14001, TNFD |
| ESRS S1 | Own workforce | L4,L11 | UC-OHS, UC-TRN | ISO 45001, ISO 30414 |
| ESRS S2–S4 | Value-chain workers, communities, consumers | L9,L8 | UC-SUP, UC-PM | ISO 26000, UNGC |
| ESRS G1 | Business conduct | L1,L3 | UC-AUD, UC-RM | ISO 37001, ISO 37301 |

## 9.4 Carbon accounting reuse (Scope 1/2/3)

`EV-GHG` (GHG inventory + assurance trail) is collected once and proves:
- ESRS E1 (EU mandatory disclosure)
- IFRS S2 (global climate disclosure)
- GHG Protocol corporate inventory
- CDP questionnaire responses
- SBTi target tracking

One emissions data set → five external obligations.

## 9.5 Evidence pack for ESG

| Evidence | Proves | Reach |
|---|---|---|
| `EV-GHG` | UC-ENV, UC-ESG | ESRS E1, IFRS S2, GHG Protocol, CDP, SBTi |
| `EV-POLICY` | UC-ESG | ESRS 2/G1, ISO 26000 |
| `EV-RISKREG` | UC-RM | IFRS S1/S2 risk, TNFD |
| `EV-AUDITREPORT` | UC-AUD, UC-ESG | CSRD limited assurance, ESRS |
| `EV-HAZARD`/`EV-TRAINLOG` | UC-OHS, UC-TRN | ESRS S1 |

## 9.6 Key conflicts (Phase 5)
- `CON-ESG-COST` — decarbonization capex vs. short-term margin → internal carbon
  price + phased transition plan, exec comp linked to validated targets.
- Greenwashing risk: every disclosure must trace to assured evidence
  (`EV-AUDITREPORT`) — CSRD mandates limited assurance, so the audit trail is
  not optional.

## 9.7 Regulatory direction
ISSB (IFRS S1/S2) is becoming the global baseline; ESRS is the EU's binding
double-materiality overlay. The engine treats ISSB as the floor and adds
jurisdiction-specific overlays (ESRS for EU, others as they emerge) — see
[10_future_roadmap.md](10_future_roadmap.md).
