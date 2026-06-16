# 01 — Architecture: The 7 Layers

Source data: [`../data/layers.json`](../data/layers.json). Each layer depends on
the one beneath it — this ordering is the architecture's core insight.

```
 LY7  Collective Wisdom        compounding org learning, conflict resolution
 LY6  Human Growth             dignity, appreciation, development
 LY5  Executive Intelligence   one truth, risk, forecast, early warning
 LY4  Knowledge                SOP, lessons learned, organizational memory
 LY3  Compliance               ISO · PDPA · safety · legal — proven
 LY2  Integrity                audit, verification, tamper-evident evidence
 LY1  Operations               people, time, tasks, fleet, procurement, docs
```

## Why the order matters
> You cannot have trustworthy **Executive Intelligence (LY5)** on top of data
> that has no **Integrity (LY2)**. You cannot have lasting **Compliance (LY3)**
> if **Operations (LY1)** don't capture reality cleanly. Most software sells you
> LY5 dashboards on LY1 data with no LY2 in between — which is why executives
> don't trust their own numbers.

NIRVA builds **bottom-up**: capture reality once at the edge → make it
verifiable → prove compliance → institutionalize knowledge → surface
intelligence → grow people → compound wisdom.

| Layer | Purpose | Domains (standards_kb) | Controls |
|---|---|---|---|
| LY1 Operations | Capture reality once, at the edge | L4,L6,L7,L9 | UC-AM, UC-CM, UC-SUP, UC-DOC |
| LY2 Integrity | Make it verifiable & tamper-evident | L18,L3,L2 | UC-AUD, UC-LOG |
| LY3 Compliance | Turn evidence into proven conformance | L3,L11,L12,L13,L20 | UC-PM, UC-OHS, UC-RM, UC-DG |
| LY4 Knowledge | Decouple know-how from individuals | L15,L4,L16 | UC-DOC, UC-TRN |
| LY5 Exec Intelligence | True real-time picture + early warning | L1,L2,L5 | UC-RM, UC-AUD |
| LY6 Human Growth | Develop people with dignity | L4,L15 | UC-TRN |
| LY7 Collective Wisdom | Compound learning across the org | L15,L16,L4 | UC-DOC, UC-AUD |

## Platform mapping (BEST GROUP tree → layers)
- **NirvaOS** modules (Executive Dashboard, Workforce, Commercial, Operations,
  Supply Chain, Finance, Governance, Administration) span LY1, LY5.
- **NirvaCore (ERP)** (HR/Payroll, CRM, Fleet, QC, Accounting, Document, ISO) is
  the LY1 + LY3/LY4 system of record.
- **NirvaGov** (ISO, PDPA, Audit, Tender) = LY2 + LY3.
- **NirvaProcure** (Procurement, Vendor, Marketplace, Dealer) = LY1 supply side.
- **NirvaCloud / NirvaDeploy** = the platform substrate (tenancy, CI/CD,
  compliance gates) — see standards_kb architecture doc 06.
- **NirvaAcademy / NirvaResearch / NirvaMedia** = LY4, LY6, LY7.
- **NOVA agents** operate across all layers as the AI workforce (doc 07).

## Design principle inherited from standards_kb
**One Data · One Evidence · Many Standards.** A fact captured at LY1 (a verified
check-in) becomes integrity evidence at LY2, satisfies multiple standards at
LY3, feeds the dashboard at LY5 — captured once, reused everywhere.
