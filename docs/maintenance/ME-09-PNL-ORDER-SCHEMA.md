# ME-09 — P&L uses the canonical order amount

## Change

`pnl_statement.py` now reads `orders.total_price` for monthly, quarterly, annual,
and returned-order totals. This matches the SQLite schema and the rest of the
reporting modules; `orders.total_amount` is not a persisted column.

## Verification

`test_pnl_statement_order_schema.py` inserts paid and returned orders into an
owned temporary database and verifies both monthly and quarterly reports.

## Boundary

This is a focused legacy-maintenance repair. It changes no schema, routes,
authentication, deployment configuration, or product ownership.
