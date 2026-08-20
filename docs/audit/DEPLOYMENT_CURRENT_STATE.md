---
title: Deployment Current State
repository: Nirvacore/Nirvasell
audited_at: 2026-08-19
audited_commit: 80eb422fa6630fb2134b4c597bf6051245be02cc
status: phase-0-review
---

# Deployment Current State — Nirvasell

Docker, Compose, Streamlit configuration, and deployment guides exist. Preserve for legacy operation until verified migration; do not modify hosting in Phase 0.

## Ownership direction

- Application-specific Dockerfiles and runtime requirements stay with the application.
- Reusable Compose modules, Terraform, future Kubernetes, broker, observability, secret-management, backup, and disaster-recovery infrastructure converge toward `nirva-infrastructure`.
- Release governance and manifests currently found in `nirva-ops` are inputs to that convergence.
- Deployment product behavior in `nirvadeploy` remains distinct from shared infrastructure definitions.

## Safety boundary

This audit does not deploy, restart, reconfigure, rotate, or delete anything. File presence proves a versioned definition exists; it does not prove the target is live, healthy, secure, backed up, or current.
