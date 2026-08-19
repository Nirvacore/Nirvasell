---
title: Current State Audit
repository: Nirvacore/Nirvasell
audited_at: 2026-08-19
audited_commit: 80eb422fa6630fb2134b4c597bf6051245be02cc
status: phase-0-review
---

# Current State — Nirvasell

## Audit rule

Only executable source, schemas, manifests, tests, workflows, and deployment definitions at commit `80eb422fa6630fb2134b4c597bf6051245be02cc` are treated as implementation evidence. Roadmaps and READMEs describe intent unless corroborated by source. No business code, schema, secret, or production configuration is changed by this audit.

## Repository snapshot

| Field | Value |
|---|---|
| Repository | Nirvacore/Nirvasell |
| Audited source branch | main |
| Documentation branch | agent/phase-0-source-audit-20260819 |
| Audited commit | 80eb422fa6630fb2134b4c597bf6051245be02cc |
| Package manager | pip |
| Repository shape | modular Python/Streamlit application |
| Strategic role | legacy commerce reference to reconcile into platform |
| Classification | REFERENCE_PORT_MISSING_ARCHIVE |
| Stack | Python, Streamlit, SQLite, Anthropic SDK, Docker |

Large Python/Streamlit commerce OS with per-user SQLite storage, 143 Streamlit page declarations, marketplace exporters, finance/CRM/inventory features, and optional Anthropic-powered helpers.

## Evidence-backed capability status

| Capability | Status | Evidence conclusion |
|---|---|---|
| Commerce operating UI | implemented | Products, orders, inventory, finance, marketing, CRM, purchasing, and operations pages exist. |
| Persistence | implemented | Per-user SQLite model exists, separate from platform tenancy. |
| AI helpers | partial | Anthropic-powered helpers exist but are BYOK/product-local. |
| Events | prototype | A local events.py module exists; no durable event bus/outbox was found. |

## Primary source evidence

| Path | Finding |
|---|---|
| `app.py` | Streamlit entry point. |
| `pages` | Primary application pages. |
| `db.py` | SQLite persistence. |
| `_ai_helpers.py` | AI helper integration. |
| `exporters` | Marketplace export adapters. |
| `NIRVACORE_V1_PLAN.md` | Repository itself records TypeScript platform convergence intent; treated as plan, not proof. |

## Boundaries

- This document records current state; it does not authorize migration.
- Preserve the current code and use strangler migration.
- Do not migrate schemas, delete code, rotate secrets, or change production configuration in Phase 0.
- A filename or roadmap statement is not proof that a feature is operational.
