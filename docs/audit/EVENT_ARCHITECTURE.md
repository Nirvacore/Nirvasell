---
title: Event Architecture
repository: Nirvacore/Nirvasell
audited_at: 2026-08-19
audited_commit: 80eb422fa6630fb2134b4c597bf6051245be02cc
status: phase-0-review
---

# Event Architecture — Nirvasell

## Verified current state

events.py and event-oriented UI logic are application-local. No durable cross-service broker or outbox was found. Future commerce events should originate from platform canonical transactions.

## Target contract

```text
Business transaction (platform)
  -> same-database transactional outbox
  -> broker operated by nirva-infrastructure
  -> idempotent platform/product/intelligence consumers
  -> trace, audit, retry, dead-letter, and replay controls
```

Every canonical event should include `event_id`, `event_type`, `schema_version`, `occurred_at`, `producer`, `tenant_id`, `organization_id`, `actor_id`, `correlation_id`, `causation_id`, `data_classification`, and a minimal payload. Events are facts, not remote commands. Sensitive payloads should use references or encrypted storage rather than broad replication.

## Phase 0 decision

Document existing transports and proposed contracts only. Do not introduce a broker, migrate state, or change production routing in this phase.
