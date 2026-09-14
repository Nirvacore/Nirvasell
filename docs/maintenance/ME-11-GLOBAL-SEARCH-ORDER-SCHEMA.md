# ME-11 — Global Search uses the canonical order amount

## Change

Global Search now selects and aggregates `orders.total_price`, matching the
persisted SQLite orders schema. The prior `total_amount` references caused
order and customer search queries to fail on initialized databases.

## Verification

`test_global_search_order_schema.py` initializes the real fulfillment columns in
an owned temporary database, inserts one order, and verifies the returned order
shape and amount.

## Boundary

Focused legacy-maintenance repair only; no schema, route, authentication,
deployment, or product-ownership changes.
