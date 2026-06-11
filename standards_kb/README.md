# Nirva Standards Knowledge Graph

> **Mission:** build the foundation knowledge base for the **Nirva Universal
> Compliance Engine** — one data model that lets a single set of controls and
> evidence satisfy *many* standards at once.
>
> **Principle:** **One Data · One Evidence · Many Standards.**

This package is the standards-intelligence layer that the Nirva product family
(NirvaCore · NirvaOS · NirvaCloud · NirvaDeploy · NirvaSell · NirvaTrade) can sit
on top of. It is a self-contained, dependency-free Python + JSON knowledge graph.

## What's inside

```
standards_kb/
├── data/                       # the machine-readable knowledge graph (JSON)
│   ├── organizations.json      # Phase 1 — 61 standards bodies & regulators
│   ├── standards.json          # Phase 2 — 73 standards / frameworks / regulations
│   ├── taxonomy.json           # Phase 3 — the universal 20-domain taxonomy
│   ├── common_requirements.json# Phase 4 — the "common DNA" (19 shared primitives)
│   ├── conflicts.json          # Phase 5 — 12 conflict/tension patterns
│   ├── controls.json           # Phase 6 — 20 universal controls + crosswalks
│   ├── evidence.json           # Universal evidence matrix (18 artifacts)
│   └── erp_mapping.json        # Universal ERP module mapping (16 modules)
├── graph.py                    # loader · validator · query layer (CLI)
├── build_reports.py            # regenerates the matrix docs from data
└── docs/                       # the 10 required deliverables (blueprints)
    ├── 01_standards_registry.md
    ├── 02_knowledge_graph.md
    ├── 03_comparison_matrix.md        (auto-generated)
    ├── 04_controls_matrix.md          (auto-generated)
    ├── 05_evidence_matrix.md          (auto-generated)
    ├── 06_compliance_architecture.md
    ├── 07_erp_mapping.md
    ├── 08_ai_governance_mapping.md
    ├── 09_esg_mapping.md
    └── 10_future_roadmap.md
```

## Quick start

```bash
# validate the whole graph + see the summary
python -m standards_kb.graph

# detailed control-reuse leverage stats
python -m standards_kb.graph --stats

# regenerate the data-driven matrix docs (03/04/05)
python -m standards_kb.build_reports

# export the full edge list for a graph DB (Neo4j / NetworkX / etc.)
python -m standards_kb.graph --export edges.json
```

## Graph model

Nodes: **Organization · Standard · Domain · Requirement · Control · Evidence ·
ERP-Module · Conflict.** Core edges:

| Edge | Meaning |
|---|---|
| `Standard —PUBLISHED_BY→ Organization` | who maintains it |
| `Standard —COVERS→ Domain` | which of the 20 universal domains it touches |
| `Requirement —APPEARS_IN→ Standard` | common DNA presence |
| `Control —IMPLEMENTS→ Requirement` | a control satisfies a requirement |
| `Control —SATISFIES→ Standard` | the crosswalk (one control → many standards) |
| `Evidence —PROVES→ Control` | one artifact proves many controls |
| `ERP-Module —RUNS_CONTROL→ Control` | where controls execute operationally |
| `Standard —TENSION_WITH→ Standard` | conflict register |

**Current scale:** 61 orgs · 73 standards · 20 domains · 19 requirements ·
20 controls · 18 evidence types · 16 ERP modules · **901 edges**, validated for
full referential integrity.

## The 10 deliverables

1. **Standards Registry** — `docs/01_standards_registry.md` + `data/organizations.json`, `data/standards.json`
2. **Standards Knowledge Graph** — `docs/02_knowledge_graph.md` + `graph.py`
3. **Standards Comparison Matrix** — `docs/03_comparison_matrix.md`
4. **Universal Controls Matrix** — `docs/04_controls_matrix.md` + `data/controls.json`
5. **Universal Evidence Matrix** — `docs/05_evidence_matrix.md` + `data/evidence.json`
6. **Universal Compliance Architecture** — `docs/06_compliance_architecture.md`
7. **Universal ERP Mapping** — `docs/07_erp_mapping.md` + `data/erp_mapping.json`
8. **AI Governance Mapping** — `docs/08_ai_governance_mapping.md`
9. **ESG Mapping** — `docs/09_esg_mapping.md`
10. **Future Standards Roadmap** — `docs/10_future_roadmap.md`

## Scope & accuracy note

Clause/article references (e.g. *ISO 27001 A.5.24*, *GDPR Art.33*) are mapped at
the **family/section level** for navigation and design — they are an
authoritative *map*, not a substitute for the licensed standard text. Always
confirm against the official published document before certification or audit.
Standard contents are summarized from public domain knowledge; the source
documents themselves are copyrighted by their respective bodies.
