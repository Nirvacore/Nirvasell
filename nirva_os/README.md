# NIRVA OS — Founder Source of Truth

> **NIRVA is not an ERP, not HR software, not payroll, not a chatbot.**
> NIRVA is the **Operating System for an organization** — uniting Operations,
> Integrity, Compliance, Knowledge, Executive Intelligence and Human Growth on
> one platform.

This package is the consolidated, machine-readable **source of truth** for NIRVA
OS and its place in **BEST GROUP**. It is built on top of, and wired into, the
[`standards_kb/`](../standards_kb/) knowledge graph — so strategy, products and
the compliance foundation are one connected system, not separate decks.

## Why it exists

BEST SERVICE (1,356+ staff, 256+ sites, cleaning / FM / security / outsource
workforce) runs today on LINE check-ins, a mountain of Excel and PDF, scattered
data, person-dependent knowledge, hard audits, and a leadership team that
struggles to see the whole picture. NIRVA uses BEST as its real-world pilot,
then productizes the result for the world.

## Philosophy (non-negotiable)

NIRVA is **not** built to catch, surveil, control, or instill fear. It is built
to increase **transparency, trust and fairness**; reduce **conflict, rework and
loss**; preserve **workers' dignity**; transfer **knowledge**; help people
**grow**; and let the organization **improve without being hostage to any
individual.**

## What's inside

```
nirva_os/
├── data/                       # machine-readable source of truth
│   ├── group_structure.json    # BEST GROUP: BEST SERVICE · NIRVA · NOVA · MUVERSE · SOUL · FUTURE
│   ├── layers.json             # the 7-layer OS stack
│   ├── products.json           # 9 NIRVA products (CHECK…WISDOM) → controls/standards
│   ├── problems.json           # Problem Atlas: 16 executive fears, fully analyzed
│   ├── blueprints.json         # 15 industry starter-kits
│   ├── competitors.json        # competitive landscape by category
│   └── revenue.json            # 10 revenue streams, cash-first sequencing
├── blueprint.py                # loader + cross-link validator (→ standards_kb)
└── docs/
    ├── 00_source_of_truth.md       # vision, philosophy, what NIRVA is/isn't
    ├── 01_architecture_7_layers.md # the stack
    ├── 02_product_suite.md         # the 9 products as a system
    ├── 03_problem_atlas.md         # the fears + root cause + prevention
    ├── 04_standards_research.md    # standards explained (purpose/docs/evidence/audit/NIRVA)
    ├── 05_industry_blueprints.md   # per-industry kits
    ├── 06_competitive_landscape.md # who's out there + the whitespace
    ├── 07_ai_first_company.md      # NOVA: running a company with an AI team
    ├── 08_data_migration.md        # "Bring Your Mess" — drag-and-drop migration
    ├── 09_revenue_gtm.md           # how to make money from ฿0
    └── 10_founder_answers.md       # ← the strategic answers (read this first)
```

## Quick start

```bash
python -m nirva_os.blueprint              # validate + summary
python -m nirva_os.blueprint --coverage   # problem→product coverage + MVP order
python -m standards_kb.graph              # the underlying standards graph
```

Both validators must pass — every product/problem/layer reference into the
standards graph (controls `UC-*`, standards) is checked, and every problem is
proven to map to at least one product.

## Current scale
6 group pillars · 7 layers · 9 products · 16 problems · 15 industry blueprints ·
8 competitor categories · 10 revenue streams — all cross-linked to **78
standards / 20 universal controls** in `standards_kb`.

## The one-paragraph pitch
Capture reality once at the edge (CHECK) → make it verifiable (AUDIT) → prove
compliance from that one evidence base (COMPLIANCE) → give leaders a true,
real-time picture with early warning (EXECUTIVE) → keep the knowledge in the
organization, not in people (DOCS/WISDOM) → and grow the people with dignity
(LIFE). **One data. One evidence. Many standards. Many businesses.**

---
*Accuracy note: competitor references and standard clause mappings are an
authoritative design map from public knowledge, not a substitute for licensed
standards or current vendor specs. Validate before use in contracts or sales.*
