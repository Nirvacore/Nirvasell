# 05 — Compliance Risk Register (Thai Context)

Source: [`../data/compliance_risks.json`](../data/compliance_risks.json). 12
risks scored on **likelihood × impact**, each tied to its Thai legal source, the
NIRVA mitigation, and the rules that enforce it (rule #6). Run
`python -m nirva_research.research --risks` for the sorted list.

## Heat map (likelihood × impact)
```
            LOW impact        MED impact              HIGH impact
  HIGH L                                        RSK-02 PDPA processing
                                                RSK-08 Ghost employees
  MED  L                  RSK-03 SSO            RSK-01 Min-wage/OT
                          RSK-04 WHT/VAT        RSK-05 Guard licensing
                          RSK-09 Work rules     RSK-06 Safety incident
                          RSK-11 Ungoverned AI  RSK-07 Procurement fraud
  LOW  L  RSK-10 Accounts                       RSK-12 ISO cert loss
```

## Top risks (act first)
| Risk | Thai source | Consequence | NIRVA mitigation |
|---|---|---|---|
| **RSK-02 Unlawful personal-data processing** | PDPA §24/26/39 | Fines to ฿5M + criminal + client offboarding | SOP-PDPA-INTAKE; consent, RoPA, breach 72h (PDPA-001/004) |
| **RSK-08 Ghost employees / fake attendance** | Internal control / contract | Payroll & billing leakage, SLA breach, fraud | SOP-WF-CHECKIN; verified-only headcount (WF-002/004) |
| **RSK-01 Underpayment vs minimum wage / OT** | LPA 2541 | Back-pay, fines, labour claims | PAY-003/004 enforce at payroll time |
| **RSK-05 Unlicensed security guards** | Security Business Act 2558 | Penalties, contract voidance, liability | ISO-003 blocks assignment without licence/training |
| **RSK-06 Occupational safety incident** | OSH Act 2554; ISO 45001 | Injury/fatality, prosecution, contract loss | SOP-FM-PTW; permit + competency + near-miss (OHS-001/002) |
| **RSK-07 Procurement fraud / bribery** | ISO 37001; ป.ป.ช. | Loss, criminal exposure, debarment | SOP-PROC-P2P; split/DD/bank checks (PROC-002/003/004) |

## Statutory-drift risks (medium, automatable)
RSK-03 (SSO), RSK-04 (WHT/VAT) and RSK-10 (accounts) are all **rate/deadline
drift** risks — the law changes, the system keeps using old values. Mitigation:
hold Thai statutory figures as **dated, configurable parameters** (see
`docs/03`), and let NIRVA flag when a parameter is past its review date. This
turns a recurring compliance exposure into a routine config task.

## Governance-of-AI risk
RSK-11 (ungoverned AI / automated decisions) is rising as NOVA scales.
Mitigation is built-in: AI-001 (human-in-the-loop for consequential decisions)
and AI-002 (full agent-action logging) — NIRVA governs its own AI with the same
engine it sells. This is both risk mitigation and a credibility asset.

## How to use this register
1. Review quarterly; re-score likelihood/impact as operations and law change.
2. For each risk, confirm the linked **rules are live** in NirvaCore.
3. Feed unresolved high-severity risks to **NIRVA EXECUTIVE** as early-warning
   indicators — the register is a live control, not a shelf document.

> **Disclaimer:** this register is a management tool, not legal advice. Thai
> statutory specifics are marked `[verify]` in the rules and must be confirmed
> against current law (RD, SSO, MoL, PDPC) before reliance.
