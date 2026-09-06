# ME-03 — Expense and return insert identifiers

Scope: a bounded legacy-maintenance repair; new production features remain in
NirvaCore per `CONTRIBUTING.md`.

## Root cause

`expenses.add()` and `returns.add()` execute an INSERT on SQLite and then read
`Connection.lastrowid`. Python's `sqlite3.Connection` has no such attribute;
the inserted identifier belongs to the cursor returned by `Connection.execute`.
The old helpers therefore raised `AttributeError` after a successful INSERT,
making callers unable to receive the record ID.

## Repair

Store the returned cursor in each helper and return `cursor.lastrowid`. No
schema, migration, validation rule, amount normalization, date behavior,
authentication, tenant routing or external integration changed.

## Regression gate

`test_expense_return_rowids.py` overrides `db._resolve_path` to a uniquely
owned temporary SQLite file, initializes the real expense/return tables, then
asserts IDs `1` and `2` plus persisted values for both helpers. The test also
restores the resolver and removes only its owned temporary directory.

```sh
python3 test_expense_return_rowids.py
python3 -m py_compile expenses.py returns.py test_expense_return_rowids.py
```

Observed locally on the repaired branch: 2/2 tests passed and compilation
passed. This is not a production database test and does not certify the full
Streamlit application or NirvaCore integration.

## Continuity boundary

The patch is based directly on NirvaSell `main` and changes only the two
existing helpers plus their focused test and maintenance note. It does not
include the duplicate tax-report hunk from PR #23 or any of PR #19's
unassembled TypeScript feature trees.
