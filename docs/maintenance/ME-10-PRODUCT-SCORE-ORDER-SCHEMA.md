# ME-10 — Product Score uses the canonical order amount

## Change

`product_score.py` now aggregates `orders.total_price`, the persisted order
amount in NirvaSell's SQLite schema. The prior `total_amount` reference caused
the product-ranking query to fail against a normal initialized database.

## Verification

`test_product_score_order_schema.py` inserts a product and paid order into an
owned temporary SQLite database and verifies revenue and quadrant output.

## Boundary

Focused legacy-maintenance repair only; no schema, route, authentication,
deployment, or product-ownership changes.
