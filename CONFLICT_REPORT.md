# CONFLICT_REPORT.md
> Phase 2 · Part 7 · 2026-06-14
> Severity: Low / Medium / High / Critical · **ไม่แก้ไขอัตโนมัติ** (Phase 2 = วาดแผนที่)

## Conflicts ที่พบ (มีหลักฐาน)
| # | Conflict | ประเภท | Severity | หลักฐาน | หมายเหตุ |
|---|---|---|---|---|---|
| C1 | Knowledge ฝังในแอปผิดบ้าน: `standards_kb`/`nirva_os`/`nirva_research` อยู่ใน commerce app `Nirvasell` | knowledge misplacement | **Medium** | โครงไฟล์ Nirvasell | เสี่ยงซ้ำ/ขัดกับ NotebookLM ถ้ามี · ยังไม่ย้าย |
| C2 | NirvaCore SoT ไม่ชัด: มี `nirvacore-v1` (repo) + `nirva_os` blueprint (ใน Nirvasell) + decisions (Claude) | repo/code ซ้ำซ้อนแนวคิด | **High** | SOURCE_OF_TRUTH_REPORT | ต้องเปิด `nirvacore-v1` ก่อนชี้ขาด |
| C3 | Decision Truth เก็บปนใน `Nirvasell` (commerce app) แทนที่บ้านกลาง | decision/code ปน | **Medium** | DECISION_LOG ฯลฯ อยู่ใน Nirvasell | ควรมี governance home แยก |
| C4 | `nirvatic` 99MB ผิดปกติ — สงสัย artifact ถูก track | repo risk | **High** | metadata 99MB (เทียบ repo อื่น 1-6MB) | ยังเปิดไม่ได้ · ยังไม่แตะ |
| C5 | ชื่อใน UI list (NirvaWealth/Fleet/Builder/manu/Core2/Research&Docs) ≠ repo จริง (มี 6) | registry/ความจำขัดกัน | **Medium** | github search = 6 repo | "ความจำของ NIRVA หาย" ตรงตาม Phase 2 |

## Conflicts ที่ "ยังตรวจไม่ได้" (รอหลักฐานจาก Mac/Cursor/Claude/NotebookLM)
| # | Conflict ที่อาจมี | ต้องใช้อะไรตรวจ | Severity (คาด) |
|---|---|---|---|
| C6 | Local code ต่างจาก GitHub (uncommitted/ahead/behind) | `local_audit.sh` (ดู uncommitted/branch) | ? |
| C7 | หลายโฟลเดอร์ = product เดียว (เช่น nirvacore หลายชุดบน Mac) | `local_audit.sh` | ? |
| C8 | Claude decisions ขัดกับ code จริง | รายการ Claude Projects | ? |
| C9 | NotebookLM knowledge ขัดกับ repo docs | รายชื่อ notebook | ? |

## ลำดับความสำคัญ (highest first)
1. **C2 (High)** — NirvaCore SoT: บล็อกทุกการตัดสิน architecture
2. **C4 (High)** — nirvatic 99MB: ความเสี่ยง repo
3. **C1/C3/C5 (Medium)** — จัดบ้าน knowledge/decision + กู้ registry memory
4. **C6-C9** — รอหลักฐาน local/external

> ⛔ ทุก conflict **บันทึกไว้เฉยๆ ยังไม่แก้** ตามกฎ Phase 2
