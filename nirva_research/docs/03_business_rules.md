# 03 — Business Rules for NirvaCore

Source: [`../data/business_rules.json`](../data/business_rules.json). 32
machine-readable `when → then` rules the engine enforces. This is rule #7 of the
mission made concrete: knowledge converted into rules NirvaCore can run.

## Rule schema
| Field | Meaning |
|---|---|
| `rule_type` | validation · alert · calculation · control · policy |
| `severity` | **block** (hard stop) · **warn** · **info** |
| `source` | the law/standard the rule enforces |
| `controls` / `standards` | links into `standards_kb` |
| `automatable` | can run with no human in the normal path |

## Coverage by domain
| Domain | Rules | Notable |
|---|--:|---|
| Payroll | 7 | record-lock, preparer≠approver, OT/SSO/WHT calc, wage floor |
| PDPA | 5 | biometric consent, RoPA, DSAR SLA, breach 72h, CCTV |
| Workforce | 4 | late alert, check-in integrity, impossible travel, headcount reconcile |
| Procurement | 4 | three-way match, PO-split, vendor DD, vendor=employee bank |
| ISO | 3 | document control, CAPA timeliness, training currency |
| Tax | 3 | WHT, VAT, tax-invoice completeness |
| CX | 2 | complaint logging+SLA, CSAT trigger |
| AI | 2 | human-in-the-loop, agent action logging |
| FM/Security (OHS) | 2 | permit-to-work, near-miss capture |

## The "block" rules (hard stops — highest value)
These prevent the costliest failures *before* they happen:
| Rule | Stops |
|---|---|
| **WF-002** | unverified check-in counting toward billable headcount (ghost/fake) |
| **PAY-001 / PAY-002** | payroll on unlocked records / self-approval (fraud) |
| **PAY-004** | paying below minimum wage (legal breach) |
| **PROC-001 / PROC-004** | unmatched payment / fictitious-vendor (employee bank) |
| **TAX-003** | issuing an incomplete tax invoice |
| **PDPA-001 / PDPA-004** | biometric capture without consent / un-notified breach |
| **OHS-001** | high-risk work without permit & competency |
| **AI-001** | a consequential AI decision without human sign-off |

## Example rule (PAY-002)
```
id:        PAY-002
when:      payroll approver == payroll preparer
then:      block approval; require a different authorized approver
type:      control     severity: block
source:    Segregation of duties / anti-fraud (COSO)
controls:  UC-AC, UC-FIN     standards: COSOIC
automatable: true
```

## Thai statutory figures — handle with care
Rules PAY-003/004/005/006 and TAX-001/002 carry Thai figures (OT multipliers,
SSO %, WHT/VAT rates, filing dates) marked **`[verify]`**. They are
implementation defaults. NirvaCore should treat these as **configurable
parameters** keyed to effective dates, so a rate change is a config update — not
a code change. This is itself a control against TAX/PAY compliance drift.
