# ME-12 — Daily Briefing uses the canonical order amount

## Change

Daily Briefing now reads `orders.total_price` for yesterday's revenue and
month-to-date revenue. This matches NirvaSell's persisted SQLite schema.

## Verification

`test_daily_briefing_order_schema.py` initializes the real order fulfillment
columns in an owned temporary database, inserts a paid order, and verifies the
yesterday summary.

## Boundary

Focused legacy-maintenance repair only; no schema, route, authentication,
deployment, or product-ownership changes.
