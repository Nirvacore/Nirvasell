# 01 — Domain Briefs (Intl Best Practice ↔ Thai Implementation)

Source: [`../data/domains.json`](../data/domains.json). Each brief: the global
best practice, the practical Thai reality, and the NIRVA recommendation. Run
`python -m nirva_research.research --brief` for live coverage counts.

> Note: business rules are tagged to their **primary enforcement domain** (e.g.
> OT rules under PAY, check-in under WF) but serve all three service lines —
> Cleaning/Security/FM inherit the WF + PAY + PDPA + ISO rule sets.

## Core domains (BEST pilot)

### Cleaning / Security / Facility (the three service lines)
- **Best practice:** ISO 9001 quality + ISO 45001 safety + site-level SLA
  management with verified delivery.
- **Thai reality:** labour-intensive, high turnover; security guards licensed
  under the Security Business Act 2558; CCTV/biometrics trigger PDPA; OT &
  minimum wage under LPA; VAT 7% + 3% WHT on service fees.
- **NIRVA:** CHECK (verified delivery) + COMPLIANCE (ISO/PDPA/safety) +
  blueprints (CLEANING/SECURITY/FACILITY). **Recommendation:** lead with
  verified headcount — it underpins both quality SLAs and billing integrity.

### Workforce Management
- **Best practice:** real-time required-vs-actual staffing, anti-fraud
  verification, standby recovery.
- **Thai reality:** deskless workers across 256+ sites on LINE check-in (no
  integrity); headcount disputes with clients.
- **NIRVA:** CHECK + EXECUTIVE. **Recommendation:** geo+liveness+device
  verification is the single highest-leverage build (AUT-01).

### Payroll
- **Best practice:** payroll from a locked, verified single source; strict
  segregation of duties; automated statutory calc.
- **Thai reality:** OT 1.5x/3x (LPA), SSO 5% (capped), WHT PND.1, provident fund
  optional — often run in Excel.
- **NIRVA:** NirvaCore.Payroll. **Recommendation:** feed payroll from CHECK;
  enforce preparer≠approver (PAY-002) and record-lock (PAY-001) day one.

### PDPA / Privacy
- **Best practice:** privacy-by-design, RoPA, consent, DSAR & breach workflows
  (ISO 27701).
- **Thai reality:** PDPA fully in force since 2022; fines to ฿5M + criminal;
  biometric check-in = **sensitive data** needing explicit consent.
- **NIRVA:** COMPLIANCE / NirvaGov.PDPA. **Recommendation:** ship consent +
  RoPA + DSAR timers alongside CHECK so verification is lawful from the start.

## High-priority domains

### Procurement
- **Best practice:** three-way match, vendor due diligence, anti-bribery (ISO 37001).
- **Thai reality:** WHT 3% services / 1% transport; tender bribery exposure (ป.ป.ช.).
- **NIRVA:** PROCURE. **Recommendation:** automate matching + fraud flags (AUT-05) — biggest ROI on leakage.

### Accounting & Tax
- **Best practice:** ICFR, reliable records, timely statutory accounts.
- **Thai reality:** TFRS/TFRS-NPAEs; e-Tax invoice; PP.30 (VAT) monthly, PND.3/53/50/51; Accounting Act + DBD filing.
- **NIRVA:** NirvaCore.Accounting. **Recommendation:** auto WHT/VAT + e-tax invoice validation (AUT-04); bank reconciliation (AUT-09).

### HR
- **Best practice:** human-capital metrics (ISO 30414), knowledge retention (ISO 30401).
- **Thai reality:** Thai-language contracts; **work rules (ข้อบังคับ) mandatory at ≥10 employees**; foreign-worker permits.
- **NIRVA:** NirvaCore.HR + NirvaAcademy. **Recommendation:** template work rules & contracts in DOCS; tie training matrix to assignment eligibility.

### Customer Experience
- **Best practice:** ISO 10002 complaints + ISO 10004 satisfaction loop.
- **Thai reality:** complaints arrive via LINE; CSAT drives renewals; SLA penalties.
- **NIRVA:** COMPLIANCE + EXECUTIVE. **Recommendation:** auto-capture LINE complaints into a tracked queue (AUT-03) — quick win.

### ISO Standards & Legal Compliance
- **Best practice:** continuous control monitoring; always-audit-ready.
- **Thai reality:** certification is a **tender prerequisite**; surveillance audits annual; broad legal surface (labour, licensing, building/fire).
- **NIRVA:** NirvaGov. **Recommendation:** one evidence base, many standards (the standards_kb engine) → never scramble for an audit again.

### AI Strategy
- **Best practice:** ISO 42001 AIMS + NIST AI RMF; human-in-the-loop.
- **Thai reality:** no standalone AI law yet — governed via PDPA + voluntary ISO 42001; ETDA guidance emerging.
- **NIRVA:** NOVA. **Recommendation:** govern NOVA under the same engine NIRVA sells (AI-001/002) — credibility + future-proofing.
