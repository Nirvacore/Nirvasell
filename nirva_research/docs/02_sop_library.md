# 02 — SOP Library

Source: [`../data/sops.json`](../data/sops.json). Implementation-ready
procedures. Each SOP names its trigger, ordered steps, the business rules it
enforces, what NIRVA automates vs the human, and **what it replaces** in BEST's
current LINE/Excel reality.

| SOP | Domain | Replaces | Automates |
|---|---|---|---|
| **SOP-WF-CHECKIN** — Site Check-in & Headcount Verification | WF | LINE check-in (no integrity) | Verify, alert, reconcile billable headcount |
| **SOP-WF-ROSTER** — Shift Rostering & No-Show Recovery | WF | Excel rosters + LINE | Roster suggestions, standby dispatch |
| **SOP-PAY-RUN** — Monthly Payroll Run | PAY | Excel payroll + manual filing | OT/SSO/WHT calc, filing prep, record lock |
| **SOP-PROC-P2P** — Procure-to-Pay | PROC | Email/paper approvals | Three-way match, fraud flags, WHT |
| **SOP-ISO-DOC** — Document & Record Control | ISO | PDF/Word versions in folders | Versioning, distribution, retention |
| **SOP-ISO-AUDIT** — Internal Audit & CAPA | ISO | Last-minute audit scramble | Evidence collection, escalation |
| **SOP-PDPA-INTAKE** — Personal-Data Intake & Consent | PDPA | PII in open Excel/LINE | Consent logging, RoPA prompts, DSAR timers |
| **SOP-CX-COMPLAINT** — Complaint Handling | CX | Complaints lost in LINE | Channel capture, SLA timers, trend alerts |
| **SOP-FM-PTW** — Permit-to-Work | FM | Paper permits | Competency/permit checks, escalation |
| **SOP-AI-AGENT** — NOVA Agent Operation & Review | AI | Ungoverned ad-hoc AI | Drafting/analysis (human owns judgment) |

## Anatomy (example: SOP-WF-CHECKIN)
- **Trigger:** worker arrives for an assigned shift.
- **Steps:** open CHECK on bound device → capture geo+liveness+timestamp → rule
  WF-002 validates integrity (quarantine if not) → supervisor sees live
  required-vs-actual, WF-001 alerts on gaps → check-out feeds payroll.
- **Enforces rules:** WF-001, WF-002, WF-003, WF-004, PDPA-001.
- **Automates:** verification, alerting, headcount reconciliation. **Human:** only
  the quarantine queue and SLA variances.
- **Standards reached:** ISO 9001, ISO 27001, PDPA.

## Design principles
- Every SOP **enforces named rules** — the procedure and the engine agree.
- Every SOP states **what it replaces** — adoption is framed as removing pain,
  not adding process.
- Every SOP draws the **automation line** — what NIRVA does vs what a human owns
  (dignity + accountability, per the NIRVA philosophy).
