# NIRVA RESEARCH — Operational Knowledge System

> The standing research / consulting layer for the Nirva ecosystem and BEST
> Group. It transforms scattered information (Excel, PDF, LINE, tribal
> knowledge) into **enterprise knowledge that NirvaCore can execute**: domain
> briefs, an SOP library, machine-readable business rules, an automation map,
> and a Thai-context compliance risk register.

This package sits on top of, and is validated against, the two foundations
already in the repo:
- [`standards_kb/`](../standards_kb/) — the standards knowledge graph (controls, standards, evidence)
- [`nirva_os/`](../nirva_os/) — the NIRVA OS blueprint (products, layers, problems)

Operational knowledge here is **wired into** those layers: every rule, SOP and
risk references the controls/standards it implements and the NIRVA product/module
that delivers it. The validator refuses to let a reference dangle.

## What's inside
```
nirva_research/
├── data/
│   ├── domains.json           # 14 domains + Thai context + owners + links
│   ├── business_rules.json    # 32 machine-readable when→then rules for NirvaCore
│   ├── sops.json              # 10 implementation-ready SOPs
│   ├── automation.json        # 12 automation opportunities (impact × complexity)
│   ├── compliance_risks.json  # 12 Thai-context risks (likelihood × impact)
│   └── payroll_rules.json     # 47-rule unified Payroll Business Rules Catalogue
├── research.py                # loader + cross-link validator + decision-ready reports
├── payroll_engine.py          # executable, config-driven payroll calc engine
├── test_payroll_engine.py     # 25 unit tests (run with plain python or pytest)
└── docs/
    ├── 00_operating_model.md       # how NIRVA RESEARCH operates (the role & rules)
    ├── 01_domain_briefs.md         # intl best practice vs Thai implementation
    ├── 02_sop_library.md
    ├── 03_business_rules.md
    ├── 04_automation_map.md
    ├── 05_compliance_risk_register.md
    └── 06_payroll_catalogue.md     # unified payroll catalogue (analysis + formulas + tables)
```

## Quick start
```bash
python -m nirva_research.research            # validate + summary
python -m nirva_research.research --brief    # decision-ready domain coverage
python -m nirva_research.research --risks    # risk register, sorted by severity
python -m nirva_research.research --payroll  # the Payroll Business Rules Catalogue
python -m nirva_research.test_payroll_engine # run the payroll engine unit tests (25)
```

## Current scale
14 domains · 32 business rules · 10 SOPs · 12 automation opportunities ·
12 compliance risks · **47 payroll rules** — all cross-linked to **78 standards /
20 controls / 9 products**, integrity-validated.

## How it serves the mission
| Mission rule | Where it lives |
|---|---|
| Real-world implementation, not theory | SOPs + business rules (executable) |
| Thai business context | `thai_context` per domain; `[verify]` statutory figures in rules |
| Intl best practice vs Thai | `docs/01_domain_briefs.md` |
| Actionable recommendations | `docs/00` decision-ready summaries |
| Automation opportunities | `automation.json` + `docs/04` |
| Compliance risks | `compliance_risks.json` + `docs/05` |
| Convert to SOPs & business rules for NirvaCore | `sops.json` + `business_rules.json` |

## Accuracy discipline
Thai statutory specifics (minimum wage, OT multipliers, SSO %, WHT/VAT rates,
filing deadlines) **change** and are marked `[verify]`. Treat them as
implementation defaults to confirm against current law (RD, SSO, MoL) — not
legal advice. Standard clause mappings are an authoritative design map, not a
substitute for the licensed standard text.
