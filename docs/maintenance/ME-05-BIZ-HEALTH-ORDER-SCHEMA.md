# ME-05 — Business Health order amount schema

Status: **implemented on a narrow repair branch; pending review**

## Problem

The canonical `orders` table stores revenue as `total_price`, while Business
Health's revenue and expense-ratio scores queried `total_amount`. Those
queries failed on the real schema instead of scoring the recorded orders.

## Change

Reuse the existing `orders.total_price` field in the three Business Health
queries. No schema migration, persistence redesign, auth, deployment, or Core
integration is included.

## Verification

- `python3 test_biz_health_revenue_schema.py` (1 passed).
- `python3 -m py_compile biz_health.py test_biz_health_revenue_schema.py`.
- `git diff --check`.
