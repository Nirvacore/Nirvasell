# 07 — The AI-First Company (NOVA)

Goal: **one founder + a team of AI agents + human review at the end.** NOVA is
the AI workforce that operates inside NIRVA. This is both how BEST GROUP runs
itself and a product.

## The operating model
```
Founder (direction, judgment, final approval)
   │
   ▼
NOVA agents (do the work, grounded in NIRVA's knowledge graph)
   │  draft · analyze · build · check
   ▼
Human review at the end (accountability, the line a human signs)
```
Principle: **AI does the 80% of drafting/analysis; humans own the 20% of
judgment and accountability.** Every agent action is logged (UC-LOG) and
governed (UC-AIG / ISO 42001) — the AI workforce is itself auditable.

## The AI org chart
| Agent | Role | Grounded in | Human reviewer |
|---|---|---|---|
| **AI CEO Assistant / Executive Agent** | Synthesizes the daily briefing, flags risks/decisions | EXECUTIVE dashboard data | Founder |
| **AI Project Manager** | Plans, tracks, unblocks work | Tasks/operations (LY1) | Founder/lead |
| **AI Business Analyst / Research Agent** | Market, competitor, standards research | NirvaResearch + knowledge graph | Founder |
| **AI Developer** | Builds features, fixes bugs | Codebase | Senior eng |
| **AI QA** | Tests, validates, finds regressions | Test suites, specs | Eng lead |
| **AI Auditor** | Checks evidence, flags control gaps | AUDIT + standards_kb | Internal auditor |
| **AI Compliance Assistant / ISO Agent** | Drafts policies, maps controls, tracks CAPA | COMPLIANCE + standards_kb | Compliance officer |
| **AI Knowledge Curator** | Keeps SOPs/lessons current, answers staff Q&A | DOCS/WISDOM (LY4/LY7) | Knowledge owner |
| **HR / Procurement / Finance Agents** | Domain ops drafting & analysis | NirvaCore modules | Function head |

## Tooling stack (what each tool is for)
| Tool | Use in NOVA |
|---|---|
| **Claude / Claude Code** | Primary build + reasoning agent (this repo is built with it) |
| **ChatGPT / Gemini** | Secondary drafting, multimodal, breadth |
| **NotebookLM** | Grounded Q&A over document corpora (SOPs, contracts) |
| **Cursor** | AI-native coding surface |
| **GitHub** | Source of truth for code + CI/CD (NirvaDeploy) |
| **MCP servers** | Connect agents to real systems (data, docs, design, search) |
| **Agent systems / automation** | Orchestrate multi-step, multi-agent workflows |

## Governance (non-optional)
NOVA is an in-scope AI system under NIRVA's own COMPLIANCE layer:
- **ISO 42001 / NIST AI RMF** — model lifecycle, impact assessment (UC-AIG)
- **Human-in-the-loop** for any consequential decision (resolves the
  automation-vs-oversight conflict, EU AI Act Art.14)
- **Logged & explainable** — every agent action produces evidence
- **Privacy-respecting** — agents touch personal data only under UC-PM/UC-AC

> NIRVA eats its own governance: the AI that runs the company is governed by the
> same compliance engine NIRVA sells. That is the credibility story.

## Why this is a moat
Generic AI is undifferentiated. NOVA is **grounded** in a specific organization's
verified operational data and a curated standards knowledge graph, **governed**
end-to-end, and **accountable** through human review. That combination —
domain + governance + accountability — is exactly what enterprises can't get
from a raw chatbot.
