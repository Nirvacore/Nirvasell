# 06 — Unified Payroll Business Rules Catalogue (BEST GROUP)

Machine-readable source: [`../data/payroll_rules.json`](../data/payroll_rules.json)
· Live view: `python -m nirva_research.research --payroll`
· **Executable engine:** [`../payroll_engine.py`](../payroll_engine.py) +
[`../test_payroll_engine.py`](../test_payroll_engine.py) (29 passing tests, incl. PIT/PND.1 & final pay) —
the formulas in §B are implemented and unit-tested, config-driven so every
`[verify]` figure is a dated parameter, not code.

> **What this is:** every payroll rule BEST GROUP needs to run a large,
> multi-site, OT-heavy **mixed daily-/monthly-paid** service workforce —
> consolidated into one catalogue NirvaCore can execute, grounded in Thai law.

---

## A. Analysis (rule #8 — what I found)

**Files analyzed:** the payroll content already in `nirva_research` —
`business_rules.json` (PAY-001…007), `sops.json` (SOP-PAY-RUN), `domains.json`
(PAY), `compliance_risks.json` (RSK-01, RSK-03). No source spreadsheets exist in
the repo yet; this catalogue is the schema those files should populate.

**Key insight:** the starter set was only **7 rules** and covered a fraction of a
real Thai payroll engine. It enforced record-lock, SoD, OT, minimum wage, SSO,
WHT and payslip protection — but had **no** coverage of working-time caps,
holiday/leave pay, the daily-vs-monthly distinction, allowance classification,
deduction limits, provident fund, WCF, severance, final-pay timing, the statutory
filing calendar, retro/rounding controls, or reconciliation.

**Missing controls now closed:** 7 → **47 rules** across 9 categories, **13 hard
‘block’ controls**. The original 7 are preserved and crosswalked (see §G).

**Decision-ready summary:**
> **Recommendation:** adopt this catalogue as the BEST GROUP payroll source of
> truth and implement the 13 `block` rules first.
> **Why:** they directly prevent the two highest-severity payroll risks —
> underpayment vs minimum wage/OT (RSK-01) and ghost/fraud leakage (RSK-08) —
> plus statutory-filing penalties (RSK-03/04).
> **Impact:** removes legal-penalty exposure and direct payroll leakage.
> **Complexity:** medium (calc engine + config table). **NIRVA:**
> NirvaCore.Payroll, fed by CHECK verified hours.

---

## B. Calculation reference (the engine)

```
Hourly rate
  monthly-paid:  hourly = monthly_salary / 30 / 8       [verify divisors]
  daily-paid:    hourly = daily_wage / 8

Overtime & holiday pay (per LPA §61–63)
  Normal-day OT ............ hourly × 1.5 × hours                 (PR-EARN-003)
  Holiday, normal hours:
     daily-paid ............ daily_wage × 2  (extra 1× the day)   (PR-EARN-004)
     monthly-paid .......... + hourly × 1.0 × hours               (PR-EARN-005)
  Holiday OT ............... hourly × 3 × hours                   (PR-EARN-006)
```

### OT / holiday multiplier matrix
| Scenario | Daily-paid (รายวัน) | Monthly-paid (รายเดือน) | Source |
|---|---|---|---|
| OT on normal working day | 1.5× hourly | 1.5× hourly | §62 |
| Work on holiday, normal hours | **2×** (gets the day they don't normally get) | **+1×** (salary already covers it) | §62/§63 |
| OT on a holiday | 3× hourly | 3× hourly | §63 |

> The daily-vs-monthly split is the #1 Thai payroll error. The catalogue encodes
> it explicitly (`applies_to`).

### PIT / PND.1 withholding (PR-DED-002) — implemented & tested
Monthly withholding uses the standard **annualization method**: annual tax on
(12 × monthly income) ÷ 12, after the employment-expense deduction and
allowances.
```
taxable = annual_income − expense_deduction − allowances
  expense   = min(50% × income, 100,000)              [verify]
  allowances= personal 60,000 (+spouse 60,000, +30,000/child,
              +SSO ≤9,000, +PF/insurance/donations)   [verify]
```
| Net taxable (THB/yr) | Marginal rate |
|---|---|
| 0 – 150,000 | 0% |
| 150,001 – 300,000 | 5% |
| 300,001 – 500,000 | 10% |
| 500,001 – 750,000 | 15% |
| 750,001 – 1,000,000 | 20% |
| 1,000,001 – 2,000,000 | 25% |
| 2,000,001 – 5,000,000 | 30% |
| > 5,000,000 | 35% |

Worked example (tested): ฿30,000/mo single earner → taxable ฿191,000 → annual
tax ฿2,050 → **฿170.83/mo**. The same earner with a non-earning spouse + 2
children falls below the ฿150,000 threshold → **฿0**. Brackets & allowances are
all config (`StatutoryConfig`), so a Revenue Code change is a parameter update.

---

## C. Severance schedule (PR-TERM-001, LPA §118)
| Continuous service | Severance (days of last wage) |
|---|---|
| 120 days – < 1 year | 30 |
| 1 – < 3 years | 90 |
| 3 – < 6 years | 180 |
| 6 – < 10 years | 240 |
| 10 – < 20 years | 300 |
| ≥ 20 years | 400 |

Plus: payment in lieu of notice (PR-TERM-002), unused annual-leave payout
(PR-TERM-004), and **final pay within 3 days** of termination (PR-TERM-003,
§70). Special severance for relocation/automation (PR-TERM-005, §120–122).

---

## D. Leave entitlements (paid)
| Leave | Statutory minimum | Rule | Source |
|---|---|---|---|
| Annual | ≥6 working days/yr after 1 yr | PR-LEAVE-001 | §30 |
| Sick | ≤30 paid days/yr (cert if ≥3 days) | PR-LEAVE-002 | §32/§57 |
| Personal/business | ≥3 paid days/yr | PR-LEAVE-003 | §34 |
| Maternity | 98 days; ≤45 paid by employer | PR-LEAVE-004 | §41/§59 |
| Military | ≤60 paid days | PR-LEAVE-005 | §35 |

---

## E. Statutory filing calendar
| Obligation | Deadline | Rule |
|---|---|---|
| PND.1 (PIT withholding) + remittance | by **7th** of next month (+e-filing days) | PR-FILE-001 |
| Social Security remittance & filing | by **15th** of next month | PR-FILE-002 |
| Provident fund remittance | per fund rules | PR-FILE-003 |
| PND.1 Kor (annual) + SSO annual wage report | year-end (≈Feb) | PR-FILE-004 |
| Workmen's Compensation Fund (employer-only) | annual cycle | PR-FILE-005 |
| WHT certificate (50 Tawi) to employee | on withholding / annual | PR-FILE-006 |

*All dates `[verify]` — hold as dated config, not code.*

---

## F. The 13 hard-stop (`block`) rules — implement first
| Rule | Stops |
|---|---|
| PR-EARN-001 | paying below provincial minimum wage |
| PR-TIME-002 | unconsented overtime |
| PR-DED-004 | over-deduction beyond §76 limits |
| PR-TERM-001 / 003 | missing/late statutory severance & final pay |
| PR-FILE-001 / 002 | late PND.1 / SSO remittance (penalties) |
| PR-CTRL-001 / 002 / 003 / 007 | unlocked records · self-approval · unverified hours · bank≠register |
| PR-DATA-001 | payslips/PII exposed (PDPA) |
| PR-AUD-002 | duplicate ID / shared bank account (ghost/fraud) |

---

## G. Crosswalk — legacy PAY-* → catalogue
| Legacy | Replaced by |
|---|---|
| PAY-001 Time-record lock | PR-CTRL-001 |
| PAY-002 Preparer ≠ approver | PR-CTRL-002 |
| PAY-003 OT calc | PR-EARN-003 + PR-EARN-006 |
| PAY-004 Minimum wage | PR-EARN-001 |
| PAY-005 Social Security | PR-DED-001 |
| PAY-006 WHT PND.1 | PR-DED-002 |
| PAY-007 Payslip protection | PR-DATA-001 |

The legacy IDs remain valid in `business_rules.json` (referenced by SOP-PAY-RUN);
the catalogue is the authoritative, expanded set. `research.py` validates the
crosswalk both ways.

---

## H. Implementation guidance for NirvaCore
1. **Config, not code.** Every `[verify]` figure (min wage, OT multipliers, SSO
   %, deduction limits, filing dates, severance bands) is a **dated parameter**
   keyed to `effective_date`. A law change = a config update + an alert when a
   parameter passes its review date. This turns statutory drift (RSK-03/04) into
   routine maintenance.
2. **Verified hours in, locked records, SoD out.** PR-CTRL-001/002/003 gate every
   run; hours come from CHECK, not manual entry.
3. **Separate ‘wage’ from ‘non-wage’.** PR-EARN-007 — only true ค่าจ้าง enters the
   OT/holiday/severance base. Get this classification signed off by Legal.
4. **One evidence pack per run.** PR-AUD-004 bundles register + bank file +
   filings + reconciliations (EV-FINCTRL) → audit-ready, SOC 1 / ISO 9001.

> **Disclaimer:** management/engineering artifact, **not legal advice**. Thai
> statutory specifics change and are marked `[verify]`; confirm against MoL, RD,
> SSO and a Thai labour lawyer before reliance.
