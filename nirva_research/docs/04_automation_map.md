# 04 — Automation Map

Source: [`../data/automation.json`](../data/automation.json). 12 opportunities
plotted on **impact × complexity** (rule #5). Sequence: quick-wins build trust &
cash; strategic items are the durable value.

## Impact × complexity quadrants
```
            LOW complexity                 HIGH complexity
  HIGH    ┌──────────────────────┐      ┌──────────────────────────┐
  impact  │ QUICK WIN             │      │ STRATEGIC                │
          │ AUT-03 LINE complaint │      │ AUT-01 Check-in verify   │
          │ AUT-07 Standby dispatch│     │ AUT-02 Payroll auto-calc │
          │ AUT-11 Bring-Your-Mess │     │ AUT-04 WHT/VAT + e-tax   │
          └──────────────────────┘      │ AUT-05 3-way match+fraud │
                                         │ AUT-06 Continuous compliance│
                                         │ AUT-10 NOVA gov. review  │
                                         │ AUT-12 Exec early-warning│
  MED     ┌──────────────────────┐      ┌──────────────────────────┐
  impact  │ (none)               │      │ FILL-IN                  │
          │                      │      │ AUT-08 PDPA consent/DSAR │
          │                      │      │ AUT-09 Bank reconciliation│
          └──────────────────────┘      └──────────────────────────┘
```

## Do-first list (quick wins — weeks, high payoff)
1. **AUT-11 Bring-Your-Mess migration** — drag-drop Excel/PDF/LINE/CSV; AI maps,
   validates, cleanses, imports with audit trail. *Removes the #1 adoption
   blocker; enables every other module.*
2. **AUT-03 LINE/email complaint capture** — stop losing complaints; protect
   renewals.
3. **AUT-07 No-show standby dispatch** — reduce SLA penalties immediately.

## Strategic builds (the durable value)
| ID | What | Business impact |
|---|---|---|
| AUT-01 | Integrity check-in verification | Eliminates ghost/buddy-punch leakage (~1–8% payroll) + protects SLA billing |
| AUT-02 | Payroll auto-calc + statutory filing | Cuts cycle time & penalty risk; enforces SoD |
| AUT-04 | WHT/VAT + e-tax invoice | Reduces tax error/penalty; audit-ready ledgers |
| AUT-05 | Three-way match + fraud flags | Cuts procurement leakage (~5–15% spend) |
| AUT-06 | Continuous control monitoring | Always-audit-ready; one evidence, many standards |
| AUT-10 | NOVA drafting + governed review | Ops leverage at low headcount, governed & auditable |
| AUT-12 | Executive early-warning analytics | See problems before they become disasters |

## Estimation method (rule #9)
Each opportunity carries `impact`, `complexity`, `quadrant` and a
`business_impact` estimate. ROI logic: **leakage/penalty avoided + hours saved +
risk removed**, against build complexity. Verification (AUT-01) and procurement
matching (AUT-05) have the clearest hard-dollar ROI (leakage) and should anchor
the business case to the BEST board.
