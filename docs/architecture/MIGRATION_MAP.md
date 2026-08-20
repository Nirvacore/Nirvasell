---
title: Migration Map
repository: Nirvacore/Nirvasell
audited_at: 2026-08-19
audited_commit: 80eb422fa6630fb2134b4c597bf6051245be02cc
status: phase-0-review
---

# Migration Map — Nirvasell

**Decision:** `REFERENCE_PORT_MISSING_ARCHIVE`  
**Target role:** legacy commerce reference to reconcile into platform

1. Treat repository as executable legacy/reference, not a second product core.
2. Create capability parity matrix with platform commerce/sell modules.
3. Port only missing behavior with tests; do not copy SQLite schema wholesale.
4. Export and reconcile historical data only after canonical mapping approval.
5. Archive after users and data are cut over.

## Strangler controls

- Keep current APIs and schemas stable while introducing adapters.
- Compare behavior and data before choosing a canonical path.
- Dual-read or shadow-compare before write cutover where risk warrants it.
- Reconcile counts, identifiers, totals, approvals, evidence, and audit trails.
- Archive only after consumer cutover, rollback window, and explicit approval.
