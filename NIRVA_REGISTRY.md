# NIRVA_REGISTRY.md — Master Ecosystem Registry
> NIRVA MASTER COMMAND CENTER · Phase 2 · 2026-06-14
> เป้าหมาย: **clarity ไม่ใช่ migration** · บทบาท = cartography (วาดแผนที่ตามจริง)
> ⚠️ ข้อจำกัด environment: audit รันบน **cloud VM** ไม่ใช่ MacBook → คอลัมน์ Local/Cursor/Claude/Knowledge ที่ยังไม่มีหลักฐาน = **`?` (Access Limitation)** ไม่ใช่ค่าว่างจริง

Classification: **A**=Production(พึ่งพาธุรกิจจริง) · **B**=Product(pre-prod) · **C**=Research/Venture · **D**=Archive · **P**=Pending Verification

## Master Table
| Business Domain | Product | Class | GitHub Repo | Local Folder | Cursor Project | Claude Project | Knowledge Source | Decision Source | Confidence | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| NIRVA | NirvaCore (ERP) | **P** | `nirvacore-v1` 🔒 | ? | ? | ? | ? | Claude (this repo) | Low | ผู้สมัคร SoT · private ยังไม่ audit |
| NIRVA | nirva.sell | **B** | `Nirvasell` ✅ | ? | ? | ? | embedded `standards_kb`,`nirva_research` | Claude (this repo) | Med | code ยืนยัน · ยังไม่ prod |
| NIRVA | NirvaProcure | **B** | `Nirvaprocure` ✅ | ? | ? | ? | repo docs (01-05_*.md) | repo STATUS.md | Med | "ready for first pilot" |
| NIRVA | NirvaDeploy | **P** | `nirvadeploy` 🔒 | ? | ? | ? | ? | ? | Low | private ยังไม่ audit |
| NIRVA | nirvatic (?) | **P** | `nirvatic` 🔒 | ? | ? | ? | ? | ? | Low | 99MB 🔴 risk · private |
| MUVERSE | Mu Tea | **C** | `MUTEA` ✅ | ? | ? | ? | `MUTEA/docs/research` | repo README | Med | venture/exploration |
| NIRVA | NirvaGov (ISO) | **P** | *(ไม่มี repo)* | ? | ? | ? | `Nirvasell/standards_kb` | Claude | Low | ยังเป็น package ฝังใน Nirvasell |
| NIRVA | NirvaOS | **P** | *(ไม่มี repo)* | ? | ? | ? | `Nirvasell/nirva_os` | Claude | Low | blueprint อยู่ใน Nirvasell |
| NIRVA | Nirva Research / Payroll | **C** | *(ไม่มี repo)* | ? | ? | ? | `Nirvasell/nirva_research` | Claude | Low | payroll_engine ฝังใน Nirvasell |
| NIRVA | NirvaCloud/Trade/Wealth/Academy/Media | – | *(ไม่มี repo)* | ? | ? | ? | ? | ? | – | แนวคิด ยังไม่มีโค้ด |
| NOVA | (ทั้งหมด) | – | *(ไม่มี repo)* | ? | ? | ? | ? | ? | – | แนวคิด |
| MUVERSE | Living/Wellness/Store... | – | *(ไม่มี repo)* | ? | ? | ? | ? | ? | – | แนวคิด |
| SOUL | (ทั้งหมด) | – | *(ไม่มี repo)* | ? | ? | ? | ? | ? | – | แนวคิด |
| BEST SERVICE | Investigation/Cleaning/Security/FM/Rental/Manpower | – | *(ไม่มี repo)* | ? | ? | ? | ? | ? | – | ธุรกิจจริง แต่ยังไม่มี repo |

## สถานะ Registry
- ✅ **Code Truth (GitHub):** 6 repo จริง — 3 audit แล้ว, 3 รอสิทธิ์
- ❓ **Local / Cursor / Claude Projects / NotebookLM:** ยังเก็บหลักฐานไม่ได้จาก cloud → ใช้ `scripts/local_audit.sh` รันบน Mac แล้วส่งผลกลับ
- ดูรายละเอียด: `REPO_AUDIT_REPORT.md`, `SOURCE_OF_TRUTH_REPORT.md`, `CONFLICT_REPORT.md`
