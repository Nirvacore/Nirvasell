---
title: Canonical Entity Map
repository: Nirvacore/Nirvasell
audited_at: 2026-08-19
audited_commit: 80eb422fa6630fb2134b4c597bf6051245be02cc
status: phase-0-review
---

# Canonical Entity Map — Nirvasell

| Concept | Current representation | Canonical owner | Decision |
|---|---|---|---|
| Product/order/inventory | db.py and commerce modules | platform | Compare with platform catalog, order, warehouse, inventory, and sell modules. |
| Customer/CRM | customer modules | platform | Reconcile with canonical Customer/Deal. |
| Finance | P&L, cash flow, expenses, invoices | platform | Keep deterministic calculations and records in platform. |
| AI helper | _ai_helpers.py and customer_ai.py | intelligence | Port useful prompts/behaviors into governed agents and evals. |

## Cross-cutting rule

Platform owns deterministic business truth. Intelligence owns derived knowledge, model/prompt configuration, agent/tool governance, citations, evaluations, and AI-run evidence. Infrastructure owns runtime services and operational controls. Product repositories may own experience-specific aggregates but should reference canonical identity, tenant, business, and audit records.
