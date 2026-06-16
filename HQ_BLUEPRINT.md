# NIRVA LIFE OS — `~/HQ` Blueprint (10-Year Plan)
> NIRVA MASTER COMMAND CENTER · 2026-06-14 · **เอกสารหลัก (canonical)**
> เป้าหมาย: ไม่สูญไฟล์ · ทุกโปรเจกต์มีบ้าน · ไฟล์ใหม่รู้ที่อยู่ · โตได้ 10 ปี · เก็บประวัติ · ลดความเครียด
> กฎเหล็ก: **ไม่ลบอัตโนมัติ · ไม่ทับอัตโนมัติ · backup ก่อนเสมอ**

## โครงราก `~/HQ/`
```
~/HQ
├── 01_CORE        # mission-critical (NirvaCore, BEST ERP) — Source of Truth
├── 02_PRODUCTS    # อาจเป็นธุรกิจ (Deploy, Procure, Wealth, Gov, Media, Academy)
├── 03_VENTURES    # สำรวจ/แบรนด์ผู้บริโภค (MuVerse, MuTea, Soul, Nova)
├── 04_KNOWLEDGE   # ทุกอย่างที่สอนเรา (ISO, Research, Prompts, NotebookLM, Docs)
├── 05_WORKSPACE   # งานชั่วคราว — ไม่มีอะไรถาวร (Inbox, Review, This_Week, Waiting)
├── 06_ARCHIVE     # เสร็จ/ไม่ใช้แล้ว — read-only (2025, 2026, Legacy, Retired)
├── 07_BACKUPS     # disaster recovery (Daily, Weekly, Monthly, Releases)
├── 08_MEDIA       # asset สร้างสรรค์ (Photos, Video, Audio, Graphics, Brands)
├── 09_PERSONAL    # ชีวิต (Family, Health, Finance, Travel, Learning)
└── 10_SYSTEM      # เครื่องมือเทคนิค (Installers, SDKs, Scripts, Configs)
```

## รายละเอียดหมวด + กฎเฉพาะ
| หมวด | บรรจุ | subfolders | กฎ |
|---|---|---|---|
| 01_CORE | NirvaCore, BEST ERP, Company Ops | `NirvaCore/` | GitHub repo คงสภาพ = SoT · ดูแลสูงสุด |
| 02_PRODUCTS | ผลิตภัณฑ์ที่อาจโต | NirvaDeploy, NirvaProcure, NirvaWealth, NirvaGov, NirvaMedia, NirvaAcademy | แต่ละตัวควรมี repo + remote |
| 03_VENTURES | exploration/consumer | MuVerse, MuTea, Soul, Nova | ทดลองได้ ความเสี่ยงต่ำ |
| 04_KNOWLEDGE | สิ่งที่สอนเรา | ISO, Research, Prompts, NotebookLM, Documentation | Knowledge Truth = NotebookLM |
| 05_WORKSPACE | ชั่วคราว | Inbox, Review, This_Week, Waiting | **ล้างทุกสัปดาห์** |
| 06_ARCHIVE | เสร็จ/นิ่ง | 2025, 2026, Legacy, Retired | **read-only** |
| 07_BACKUPS | กู้ภัย | Daily, Weekly, Monthly, Releases | retention ด้านล่าง |
| 08_MEDIA | ครีเอทีฟ | Photos, Video, Audio, Graphics, Brands | |
| 09_PERSONAL | ชีวิต | Family, Health, Finance, Travel, Learning | ส่วนตัว |
| 10_SYSTEM | เครื่องมือ | Installers, SDKs, Scripts, Configs | |

## Retention (07_BACKUPS)
- Daily: 7 วัน · Weekly: 4 สัปดาห์ · Monthly: 12 เดือน · **Releases: ตลอดไป**

## Policies
**Downloads:** ไม่ใช่ Source of Truth · เป็น *inbox* เท่านั้น · อะไรเก่ากว่า **30 วัน ต้องย้ายออก**
**New File (ถามก่อนวาง):** ถาวร? → 01/02/03 · ความรู้? → 04 · ชั่วคราว? → 05 · backup? → 07 · สื่อ? → 08 · ส่วนตัว? → 09
**Truth hierarchy:** Code=GitHub · Decision=Claude · Knowledge=NotebookLM · Workspace=MacBook
**NAS (Synology):** long-term storage · backup `HQ` + databases + media **ทุกคืน** · เก็บ snapshot รายเดือน
**Yearly review:** ทบทวน Archive/Products/Ventures · ปรับโครง · ไม่สะสมความรก

## หลักการสุดท้าย
> ไม่ใช่แค่จัดไฟล์ — นี่คือ **ระบบปฏิบัติการของชีวิต** · เป้าหมายไม่ใช่ความสมบูรณ์แบบ แต่คือ **clarity · resilience · peace**

---
**สถานะ:** blueprint นี้ = แบบหลัก · การลงมือดู `MAC_REORGANIZATION_PLAN.md` + สคริปต์ `hq_init.sh`/`nirva_backup.sh`/`nirva_reorg.sh` (default DRY-RUN · ยังไม่ execute)
