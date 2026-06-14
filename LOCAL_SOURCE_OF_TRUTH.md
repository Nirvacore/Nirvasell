# LOCAL_SOURCE_OF_TRUTH.md
> Phase 2A · 2026-06-14 · ฐาน: รายการที่ผู้ใช้รายงาน (ยืนยันด้วยสคริปต์)

## 🚨 HIGH RISK — Downloads อาจมี production asset
**พบสัญญาณ:** `~/Downloads/` มี `nirva deploy`, `deploy`, `nirva_deploy.zip`, `nirva-landing`, `NirvaGovTH Dev Spec.docx`

**คำตัดสิน:** ถ้าโฟลเดอร์ deploy เหล่านี้คือโค้ดที่ใช้ deploy จริง → **🔴 HIGH RISK**
**เหตุผล (ตาม Phase 2):** *Downloads ต้องไม่กลายเป็น Source of Truth* — มันคือพื้นที่ชั่วคราว ถูกล้าง/ทับ/ลบง่าย ไม่มี backup, ปนของอื่น
**ต้องยืนยัน:** สมาชิก Downloads มี `.git` + remote ไหม (ถ้าไม่มี = ลอย ไม่ backup = ยิ่งเสี่ยง)

## SoT candidate ต่อ component (provisional)
| Component | local candidate | remote (Code Truth) | สถานะ SoT |
|---|---|---|---|
| NirvaCore | `~/nirvacore` หรือ `~/NIRVA` | `nirvacore-v1` 🔒 | **UNRESOLVED** (ดู Phase 2B) |
| NirvaDeploy | `~/Downloads/nirva deploy` ⚠️ | `nirvadeploy` 🔒 | เสี่ยง — local อยู่ใน Downloads |
| NirvaWealth | `~/nirvawealth` | **ไม่มี repo** | local-only → ยังไม่ backup cloud |
| Mu Tea | `~/mu-tea` | `MUTEA` | remote มี → GitHub = SoT ที่ปลอดภัยกว่า |
| NirvaGov | `~/Downloads/...docx`, `~/Doc.for.ERP` | ไม่มี repo | knowledge ลอย |
| Decisions | `~/Claude`, `~/Documents/Claude` | this repo (`Nirvasell`) | กระจาย → ต้องรวมบ้าน (ภายหลัง) |

## หลักการ SoT (ย้ำ)
- **Code Truth = GitHub** (ปลอดภัยสุด มี backup) → ตัวที่มี remote ควรถือ GitHub เป็น SoT
- **local-only (เช่น nirvawealth)** = ความเสี่ยง: ถ้า Mac พัง = สูญ → *ควร push ขึ้น GitHub* (แต่ยังไม่ทำใน phase นี้)
- **Downloads = ห้ามเป็น SoT เด็ดขาด**

## Proposed future structure (ℹ️ informational only — ยังไม่ทำ)
```
~/NIRVA/
├── core/        # nirvacore (ตัวจริงหลังยืนยัน L1)
├── deploy/      # nirva deploy (ย้ายออกจาก Downloads)
├── wealth/      # nirvawealth (+ สร้าง repo)
├── muverse/     # mu-tea
├── soul/        # (ยังไม่มี)
├── docs/        # Doc.for.ERP, NirvaGovTH spec, Claude decisions
└── archive/     # nirva-backup-*, nirva-archive, *.zip
```
> ⛔ ข้อเสนอนี้ **เพื่อดูภาพเท่านั้น** — ไม่ย้าย ไม่สร้าง ไม่ลบ ใน Phase 2A
