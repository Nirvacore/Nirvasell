# Output 8 — AI Governance Mapping

How the knowledge graph governs AI systems end-to-end, harmonizing the major AI
frameworks onto one control (`UC-AIG`) and one evidence pack.

## 8.1 The AI standards landscape (Domain L14)

| Standard | Body | Nature | Role |
|---|---|---|---|
| **ISO/IEC 42001:2023** | ISO/IEC | Certifiable management system (AIMS) | The "ISO 27001 of AI" — governance backbone |
| **ISO/IEC 23894:2023** | ISO/IEC | Guidance | AI risk management (applies ISO 31000) |
| **ISO/IEC TR 24028** | ISO/IEC | Technical report | Trustworthiness concepts |
| **NIST AI RMF 1.0** | NIST | Voluntary framework | Govern · Map · Measure · Manage |
| **EU AI Act (2024/1689)** | EU | Binding regulation | Risk-tiered legal obligations |
| **OECD AI Principles** | OECD | Principles | Values baseline (adopted globally) |
| **OWASP LLM Top 10** | OWASP | Threat guidance | LLM-specific security risks |
| **MITRE ATLAS** | MITRE | Knowledge base | Adversarial ML tactics |

## 8.2 Crosswalk — one control, the whole landscape

`UC-AIG` (AI Governance & Model Lifecycle) satisfies all of:

| Framework | Where UC-AIG maps |
|---|---|
| ISO/IEC 42001 | Full AIMS (clauses 4–10 + Annex A controls) |
| NIST AI RMF | Govern / Map / Measure / Manage functions |
| EU AI Act | Art. 9 (risk mgmt), 10 (data governance), 11–12 (documentation/logging), 13 (transparency), 14 (human oversight), 15 (accuracy/robustness), 17 (QMS) |
| ISO/IEC 23894 | AI risk process |
| OECD AI | Principles operationalized |
| OWASP LLM Top 10 | LLM01–LLM10 security controls |

## 8.3 EU AI Act risk tiers → engine behavior

| Tier | Examples | Engine action |
|---|---|---|
| **Prohibited** | Social scoring, manipulative AI | Block at intake; `UC-AIG` gate fails. |
| **High-risk** | HR screening, credit, biometric | Full obligations: conformity assessment, technical docs, human oversight (`CON-AUTOMATION-HUMAN`), post-market monitoring. |
| **Limited** | Chatbots, deepfakes | Transparency/disclosure obligations. |
| **Minimal** | Spam filters, game AI | Voluntary codes of conduct. |

## 8.4 Evidence pack for AI compliance

| Evidence | Proves | Satisfies (examples) |
|---|---|---|
| `EV-MODELCARD` (model card, AIA, eval results) | UC-AIG | ISO 42001 Annex A, EU AI Act Art.11, NIST AI RMF Measure |
| `EV-RISKREG` (AI entries in risk register) | UC-AIG, UC-RM | ISO 23894, EU AI Act Art.9 |
| `EV-POLICY` (responsible-AI policy) | UC-AIG | ISO 42001 §5.2, OECD Principles |
| `EV-RACI` (AI accountability owners) | UC-AIG | ISO 42001 §5.3, NIST AI RMF Govern |
| `EV-LOGS` (model/inference logs) | UC-AIG, UC-LOG | EU AI Act Art.12, OWASP LLM |
| `EV-TRAINLOG` (AI literacy training) | UC-TRN | EU AI Act Art.4 (AI literacy) |

## 8.5 AI lifecycle ↔ controls

```
Intake/Use-case → Impact assessment (AIA) → Data governance → Model dev/eval
   → Human oversight design → Deployment → Monitoring/drift → Decommission
        every stage logged as EV-MODELCARD / EV-LOGS under UC-AIG
```

## 8.6 Key conflicts to manage (Phase 5)
- `CON-AUTOMATION-HUMAN` — efficiency vs. mandated human oversight (Art.14).
- `CON-TRANSPARENCY-IP` — disclosure duties vs. model IP/trade secrets.
- AI governance must itself respect privacy (`UC-PM`) and security (`UC-AC`,
  `UC-LOG`) — AI is not a carve-out from the rest of the graph.

## 8.7 Self-governance note
The Nirva engine's own AI copilots (policy drafting, mapping suggestions) are
in-scope AI systems and are governed by `UC-AIG` — a deliberate "eat your own
governance" stance that produces live evidence for the platform's own AIMS.
