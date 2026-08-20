---
document_id: "NIRVA-MIG-102"
title: "NirvaSell Source-to-Platform Migration Plan"
version: "v1.0"
status: "Approved for Phase 0 planning"
owner: "Nirvacore/Nirvasell product owner"
reviewer: "NIRVA Architecture Council"
approver: "Founder / authorized architecture owner"
effective_date: "pending-approval"
review_date: "2027-08-20"
updated: "2026-08-20"
---

# NirvaSell Source-to-Platform Migration Plan

## Decision

Treat Streamlit/SQLite as executable legacy and port only missing behavior.

## Owns

Legacy seller experience and per-user data until cutover.

## Explicitly excludes

Long-term duplicate catalog/order/inventory/CRM/finance identity masters.

## Source evidence

This plan is constrained by [CURRENT_STATE.md](../audit/CURRENT_STATE.md), [GAP_ANALYSIS.md](../audit/GAP_ANALYSIS.md), [CANONICAL_ENTITY_MAP.md](./CANONICAL_ENTITY_MAP.md), and [MIGRATION_MAP.md](./MIGRATION_MAP.md). Those documents identify the audited source commit and evidence paths.
