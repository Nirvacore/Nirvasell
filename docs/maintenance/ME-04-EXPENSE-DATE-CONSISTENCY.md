# ME-04 — Expense date consistency

Status: **implemented on a narrow repair branch; pending review**

## Problem

The canonical `expenses` table has a `date` column. Cash Flow, Budget Tracker,
and Business Health still queried the removed `expense_date` name. Cash Flow
failed with SQLite `no such column`; the other reports could silently return
zero or incomplete expense data.

## Change

Reuse the existing `expenses` schema and replace only the stale column
references. No migration, persistence redesign, auth change, or Core
integration is included.

## Verification

- Red before the fix: `sqlite3.OperationalError: no such column: expense_date`.
- Green after the fix: `python3 test_expense_date_consistency.py` (1 passed).
- `python3 -m py_compile cash_flow.py budget_tracker.py biz_health.py test_expense_date_consistency.py`.
- `git diff --check`.

## Follow-up

Other modules still contain historical `expense_date` references and should be
handled as separate, testable slices after this one is reviewed; this patch
does not claim whole-application completion.
