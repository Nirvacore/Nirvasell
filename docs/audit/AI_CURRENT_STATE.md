---
title: AI Current State Audit
repository: Nirvacore/Nirvasell
audited_at: 2026-08-19
audited_commit: 80eb422fa6630fb2134b4c597bf6051245be02cc
status: phase-0-review
---

# AI Current State — Nirvasell

Optional Anthropic/BYOK features exist. Finance and legal calculations remain deterministic platform capabilities; seller assistants, forecasting explanations, content agents, RAG, and evaluations belong in intelligence.

## Strategic ownership rule

| Concern | Canonical owner |
|---|---|
| Finance/Legal deterministic calculations, ledgers, records, workflows, approvals, policies, evidence, audit | nirva-platform (evolving from nirvacore-v1) |
| Finance/Legal agents, RAG, MCP tools, prompt/model registries, citations, hallucination tests, red-team tests, evaluations | nirva-intelligence (evolving from nirva-AI) |
| Model/runtime infrastructure, Qdrant, LiteLLM, telemetry, secrets, backup | nirva-infrastructure |

## Governance minimum before production AI

- Platform-issued user, organization, tenant, role, policy, and correlation context.
- Tool registry with owner, version, risk, read/write class, permission, scope, approval, rate limit, timeout, data classification, and audit level.
- Versioned prompt/model/knowledge inputs with source provenance and citations.
- Offline and release evaluations, hallucination tests, red-team tests, and promotion approval.
- Immutable AI run, tool, approval, evidence, cost, and outcome audit records.
