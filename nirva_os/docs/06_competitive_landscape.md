# 06 — Competitive Landscape

Source: [`../data/competitors.json`](../data/competitors.json).

> **Method note:** rather than fabricate 100 shallow profiles (10 companies ×
> 10 countries), this is a defensible synthesis of well-known global leaders per
> category (collectively spanning US/CN/JP/KR/SG/DE/UK/FR/IN/AU) plus the
> recurring, widely-reported customer complaints and the resulting NIRVA
> opportunity. Vendor specifics must be re-validated before sales use.

## Category map
| Category | Representative leaders | The recurring complaint | NIRVA opportunity |
|---|---|---|---|
| **ERP** | SAP, Oracle, MS Dynamics, Workday, Odoo, Zoho, Sage | Expensive, slow, rigid, bad frontline UX, not for blue-collar/site | Frontline-first, fast-deploy OS for labour-intensive services; "bring your mess" migration |
| **Compliance / GRC** | ServiceNow, Vanta, Drata, OneTrust, AuditBoard | Tech/cloud-only; weak for physical & field ops; not PDPA/SEA-localized | Compliance for physical workforce + PDPA/Thai + one-evidence-many-standards |
| **Workforce / Field** | Connecteam, Deputy, When-I-Work, Quinyx, ZKTeco, Jibble | Weak fraud-proofing; no contract-headcount verification; no integrity layer | Integrity-grade verification tied to CONTRACT headcount + audit trail |
| **Facility Mgmt** | IBM Maximo, Planon, FSI, Fracttal, UpKeep | Heavy, costly, built for asset owner not service provider | Unified workforce+asset+compliance for the FM contractor |
| **AI / Agents** | OpenAI, Anthropic, Gemini, Copilot, Cursor, Glean | Generic, no org memory/governance, hallucination, no guardrails | NOVA: domain-grounded agents on a governed knowledge graph (ISO 42001) |
| **Exec Intelligence / BI** | Power BI, Tableau, Qlik, Looker, Domo | Needs clean data first; backward-looking; needs analysts | Decision-ready layer on data NIRVA captures clean at the edge |
| **Knowledge Mgmt** | Notion, Confluence, Guru, NotebookLM | Becomes stale graveyard; disconnected from ops/compliance | Knowledge tied to live ops + evidence; succession/handover |
| **Operational Excellence / QMS** | MasterControl, ETQ, Intelex, Qualio | Manufacturing-centric, heavy, siloed | Service-industry QMS integrated with workforce verification |

## The meta-gap (NIRVA's thesis)
Across **every** category the gap is the same:

1. **Point solutions** that don't connect Operations → Integrity → Compliance →
   Intelligence. Customers buy 6 tools and integrate none of them.
2. They **ignore the deskless, labour-intensive service workforce** in emerging
   markets — exactly BEST's world.
3. They assume **clean data already exists**; in reality SMEs live in
   LINE/Excel/PDF chaos.

NIRVA wins by being the **connected OS** that captures clean data at the edge,
for the workforce everyone else ignores, in the region (SEA/PDPA) the global
players under-serve.

## Where NOT to fight
- Don't out-feature SAP/Oracle at the enterprise-ERP core. Win the frontline +
  integrity + compliance layer they're weak at, and integrate where needed.
- Don't out-model OpenAI/Anthropic on raw AI. Win on **domain grounding +
  governance** (NOVA on the knowledge graph) — use their models, don't rebuild them.

## Per-country deep dive (roadmap, not fabricated here)
A genuine 10-companies-×-10-countries study is a research deliverable worth
doing with live sources before fundraising/positioning. It is scoped in
[10_founder_answers.md](10_founder_answers.md) under "what NIRVA still lacks"
rather than invented here — accuracy over volume.
