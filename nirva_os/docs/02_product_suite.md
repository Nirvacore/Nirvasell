# 02 — Product Suite

Source: [`../data/products.json`](../data/products.json). Nine products that
package the platform. Each is sellable alone (land) and stronger together
(expand). Validated mapping to problems, controls and standards via
`python -m nirva_os.blueprint --coverage`.

| Product | Layer | What it sells | Buyer | MVP | Time-to-revenue |
|---|---|---|---|:-:|---|
| **NIRVA CHECK** | LY1 | Trustworthy digital check-in & workforce/headcount verification | Ops Director / FM provider | **1** | days–weeks |
| **NIRVA EXECUTIVE** | LY5 | One screen of truth + AI daily briefing + early warning | CEO / MD / Board | **2** | weeks |
| **NIRVA DIAGNOSIS** | LY5 | Organizational CT scan / readiness assessment (consulting) | CEO / new mgmt | **3** | days (cash now) |
| **NIRVA AUDIT** | LY2 | Internal audit + evidence management + unbreakable trail | Auditor / CFO | 4 | weeks |
| **NIRVA PROCURE** | LY1 | Request→PO with budget control & procurement audit | Procurement / CFO | 5 | weeks–months |
| **NIRVA DOCS** | LY4 | Living SOPs, policies, contracts, document control | QMR / ISO mgr | 6 | weeks |
| **NIRVA COMPLIANCE** | LY3 | ISO + PDPA + safety from one evidence base | Compliance / DPO | 7 | months |
| **NIRVA LIFE** | LY6 | Human growth — appreciation, learning, development | HR Director | 8 | months |
| **NIRVA WISDOM** | LY7 | Org learning, lessons, conflict resolution, transfer | CEO / HR | 9 | long |

## The land-and-expand motion
```
DIAGNOSIS (consulting, cash today)
   └─► reveals the pains, produces the data, earns trust
CHECK (cheap, urgent wedge)
   └─► captures clean edge data on real workforce
EXECUTIVE (premium, buyer with budget)
   └─► turns CHECK data into board-level value
AUDIT + PROCURE + COMPLIANCE (highest ROI, sticky)
   └─► fraud/leakage reduction + always-audit-ready
DOCS + LIFE + WISDOM (retention, knowledge, dignity)
   └─► the moat: the org now runs ON NIRVA
```

## How the products reinforce each other
- **CHECK feeds EXECUTIVE**: you can't have a real dashboard without real edge data.
- **CHECK + PROCURE feed AUDIT**: verified attendance and clean POs are the evidence audit needs.
- **AUDIT feeds COMPLIANCE**: evidence + audit trail = always-audit-ready.
- **DOCS feeds WISDOM + LIFE**: SOPs become training becomes growth becomes memory.
- **Everything feeds EXECUTIVE + DIAGNOSIS**: the more layers live, the truer the picture.

## Coverage proof (auto-generated)
Run `python -m nirva_os.blueprint --coverage` — every one of the 16 executive
fears in the Problem Atlas maps to at least one product, and each product's
controls reach 7–20 standards through the standards graph.
