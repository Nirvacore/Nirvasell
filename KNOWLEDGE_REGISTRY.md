# KNOWLEDGE_REGISTRY.md
> Phase 2 · Part 4 (Knowledge Audit) · 2026-06-14

## ✅ Knowledge ที่พิสูจน์ได้ (มีหลักฐานในโค้ด)
| Knowledge repo | Domain | Scope | Update freq (จาก git) | สัมพันธ์กับ product | ตำแหน่ง | Class |
|---|---|---|---|---|---|---|
| `standards_kb/` | ISO / มาตรฐาน + knowledge graph | `graph.py`, `build_reports.py`, `data/`, `docs/` | ตาม Nirvasell (17 commits) | ป้อน **NirvaGov (ISO)** | ฝังใน `Nirvasell` | C |
| `nirva_research/` | research + **payroll** | `research.py`, `payroll_engine.py` (+test), `data/`, `docs/` | ตาม Nirvasell | ป้อน **Nirva Research + HR/Payroll** | ฝังใน `Nirvasell` | C |
| `nirva_os/` | OS blueprint | `blueprint.py`, `data/`, `docs/` | ตาม Nirvasell | ป้อน **NirvaOS/Core** | ฝังใน `Nirvasell` | C/B |
| `MUTEA/docs/` | Mu Tea brand + research | 4 research reports + brand docs | 2 commits | ป้อน **Mu Tea (MUVERSE)** | repo `MUTEA` | C |
| `Nirvaprocure/docs` + `01-05_*.md` | procurement vision/arch | vision, architecture, roadmap, tech, features | 75 commits | ป้อน **NirvaProcure** | repo `Nirvaprocure` | C(in-repo) |

## ⚠️ Access Limitation — NotebookLM
**NotebookLM** = Knowledge Truth ตาม hierarchy แต่ session นี้ **เข้าถึงไม่ได้** (ไม่มี API/credential ใน environment)
→ ต้องให้คุณส่งรายชื่อ notebook + ขอบเขต มาเติม

## Template — NotebookLM / knowledge ภายนอก
| Notebook | Owner | Domain | Scope | Update freq | สัมพันธ์กับ product |
|---|---|---|---|---|---|
| _(รอข้อมูล)_ | | | | | |

## ข้อสังเกต (governance)
- knowledge 3 ก้อน (`standards_kb`, `nirva_research`, `nirva_os`) **ฝังอยู่ใน commerce app (Nirvasell)** = misplacement → ควรมีบ้าน knowledge แยกในอนาคต (เช่น NotebookLM หรือ repo เฉพาะ) — **ยังไม่ย้าย**
- ยังไม่มีหลักฐานว่า NotebookLM ↔ repo เหล่านี้ sync กันอยู่ → เป็นความเสี่ยง "knowledge ซ้ำ/ขัดกัน" (ดู CONFLICT_REPORT.md)
