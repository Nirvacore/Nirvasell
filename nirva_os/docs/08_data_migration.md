# 08 — Data Migration: "Bring Your Mess"

> **Principle: Bring Your Mess — NIRVA Will Organize It.**

Onboarding is where most ERP/compliance projects die (6–18 months of data
cleanup). NIRVA's wedge is the **easiest migration in the world**: drag a pile
of files in, AI does the rest. This directly attacks the biggest adoption
barrier for BEST and every SME like it.

## The promise
```
Drag in:  Excel · PDF · Word · LINE export · Email · CSV · photos
          (the literal mess BEST has today)
              │
              ▼
   ┌──────────────────────────────────────────────┐
   │  AI Migration Pipeline                         │
   │  1. Ingest      detect file type & structure   │
   │  2. Mapping     AI maps columns/fields → schema│
   │  3. Validation  flag conflicts, dupes, gaps    │
   │  4. Cleansing   normalize names, dates, IDs    │
   │  5. Error detection  surface what needs a human│
   │  6. Import      load into NirvaCore, with audit│
   └──────────────────────────────────────────────┘
              │
              ▼
   Clean, structured, audit-trailed data in NIRVA
```

## Pipeline stages
| Stage | What the AI does | Human role |
|---|---|---|
| **Ingest** | Parse Excel/CSV/PDF/Word/LINE/email; OCR scans | Drop the files |
| **AI Mapping** | Infer which columns are name/ID/site/date/amount; map to NIRVA schema | Confirm/adjust the mapping (one screen) |
| **AI Validation** | Detect duplicates, impossible values, broken references, missing required fields | Review flagged items |
| **AI Cleansing** | Normalize names, dates, phone/ID formats, site codes | Approve transformations |
| **AI Error Detection** | Score confidence; quarantine low-confidence rows | Resolve the quarantine queue |
| **Import** | Commit to NirvaCore with full audit trail (UC-LOG) | Sign off |

## Why LINE export matters specifically
BEST's reality today is **LINE check-in**. A LINE chat export is messy
semi-structured text — exactly what an LLM is good at parsing. NIRVA turning a
LINE export into a clean attendance dataset is a *demo that sells itself* to
every Thai service business.

## Design rules
- **Never lose the original.** Raw files are retained as source evidence
  (resolves audit + dispute needs; supports the integrity layer).
- **Every transformation is logged.** Migration is itself audit-trailed — you
  can prove how a number got into the system.
- **Confidence-gated.** High-confidence rows auto-import; low-confidence rows
  wait for a human. No silent guessing.
- **Privacy-aware.** PII detected during ingest is classified and protected
  under UC-PM/UC-DG from the first second.

## Reuse from the existing codebase
`nirva.sell` already contains real ingest DNA: `intake.py`, `parser.py`,
`order_import.py`, `vision.py` (image/OCR), and `exporters/`. The migration
pipeline productizes and generalizes these into a "drop anything" front door.

## Strategic effect
"Bring Your Mess" collapses time-to-value from months to hours, which:
1. removes the #1 adoption objection,
2. makes the **Consulting → CHECK** on-ramp (doc 09) frictionless,
3. and immediately captures the data that powers EXECUTIVE and COMPLIANCE.
