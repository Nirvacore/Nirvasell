# HEART_REPORT.md — Find the Heart of NIRVA
> Phase 2B · focus: `~/nirvacore` และ `~/NIRVA` เท่านั้น · 2026-06-14
> No change · No cleanup · No migration · No assumptions

## ⚠️ Access Limitation (ตอบ Q1-5 ด้วยหลักฐานยังไม่ได้)
ตรวจแล้ว: `~/nirvacore` และ `~/NIRVA` **ไม่มีบน VM นี้** (session = cloud, ไม่ใช่ MacBook)
→ ผม **detect .git/remote/branch/package.json/Docker/Prisma/README/src-apps-packages/node_modules ไม่ได้จากที่นี่**
→ การตอบ "หัวใจคือโฟลเดอร์ไหน" โดยไม่มีไฟล์จริง = ผิดกฎ *No assumptions* → **ไม่ทำ**

## ✅ วิธีหาหัวใจ (รัน 1 คำสั่งบน Mac)
```bash
bash scripts/find_heart.sh > nirva_heart_$(date +%Y%m%d).txt
```
สคริปต์เจาะ **เฉพาะ 2 โฟลเดอร์** (ไม่สแกนทั้งเครื่อง) เก็บครบทุก field ที่ Phase 2B สั่ง — ส่งไฟล์กลับมา ผมเติมผลด้านล่าง + ตอบ Q1-5 ทันที

---

## Decision Rule (จะใช้ตัดสินอัตโนมัติเมื่อได้ข้อมูล)
| คำถาม | เกณฑ์ชี้ขาด (จากผลสคริปต์) |
|---|---|
| **Q1 — ERP สมบูรณ์สุด?** | โฟลเดอร์ที่มี **src/apps/packages + จำนวนไฟล์ .ts/.py มากสุด + Prisma/Docker + package.json** |
| **Q2 — เชื่อม GitHub?** | โฟลเดอร์ที่ `.git=yes` และ `remote origin` ชี้ `Nirvacore/...` (น่าจะ `nirvacore-v1`) |
| **Q3 — พัฒนา active ล่าสุด?** | `last_commit` ใหม่สุด + `uncommitted` มี activity + `newest_file` ล่าสุด |
| **Q4 — ใช้กู้ NIRVA ถ้า Mac พังวันนี้?** | ตัวที่ **(Q1 สมบูรณ์) AND (Q2 มี remote)** — ถ้า remote ครบ → กู้จาก GitHub ได้; ถ้า local-only → ตัวนั้นคือจุดเสี่ยงสูญ |
| **Q5 — ระบุ SoT ของ NirvaCore ได้ไหม?** | ได้ก็ต่อเมื่อ 1 โฟลเดอร์ชนะทั้ง Q1+Q2+Q3 อย่างชัด; ถ้าขัดกัน (เช่น สมบูรณ์อยู่ local แต่ remote ตามหลัง) → **UNRESOLVED + conflict** |

## ตารางผล (รอเติมจาก Mac)
| field | `~/nirvacore` | `~/NIRVA` |
|---|---|---|
| .git / remote / branch | PENDING | PENDING |
| last_commit / commits / uncommitted | PENDING | PENDING |
| package.json / Docker / Prisma / README | PENDING | PENDING |
| src / apps / packages | PENDING | PENDING |
| node_modules | PENDING | PENDING |
| ไฟล์โค้ด (.ts/.py/.sql/.prisma) | PENDING | PENDING |
| last modified activity | PENDING | PENDING |

## คำตอบชั่วคราว Q1-Q5
1. ERP สมบูรณ์สุด → **PENDING**
2. เชื่อม GitHub → **PENDING** (ผู้สมัคร: ตัวที่ remote = `nirvacore-v1`)
3. active สุด → **PENDING**
4. ใช้กู้ → **PENDING**
5. NirvaCore SoT → **ยังระบุไม่ได้ (UNRESOLVED)** จนกว่าจะได้ผล `find_heart.sh`
