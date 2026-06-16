# BEST_BACKUP_PLAN.md
> BEST GROUP Back Office · 2026-06-14 · **backup ก่อนแตะอะไรทั้งสิ้น (กฎข้อ 1)**

## หลักการ
- backup **ก่อน** จัดโครง/ย้ายทุกครั้ง · ไม่ลบของเดิม · เก็บ snapshot อ่านได้
- ของผูกพันกฎหมาย (6Job, 4Document) + PDPA (09_HR) = **ทำ Release backup ถาวร**
- ⚠️ **HR/PDPA: ห้าม backup ขึ้น cloud/GitHub สาธารณะ** — เก็บใน NAS/ดิสก์เข้ารหัสเท่านั้น

## ปลายทาง & Retention (`99_BACKUP/`)
| ชั้น | เก็บ | ใช้กับ |
|---|---|---|
| Daily | 7 วัน | งานประจำวัน |
| Weekly | 4 สัปดาห์ | สรุปสัปดาห์ |
| Monthly | 12 เดือน | ปิดเดือน |
| **Releases** | **ตลอดไป** | สัญญา/ลูกค้า/ISO/ภาษี/ปิดปี |

## คำสั่ง backup (ทบทวนก่อน — รันบน Mac, ตั้ง BEST_ROOT)
```bash
# DRY-RUN (ดูเฉยๆ):
BEST_ROOT="/path/to/BEST" bash scripts/best_backup.sh
# ทำจริง:
EXECUTE=1 BEST_ROOT="/path/to/BEST" bash scripts/best_backup.sh
```
สคริปต์ tar แต่ละโฟลเดอร์ → `~/BEST-HQ/99_BACKUP/Daily/<วันที่>/` (default DRY-RUN)

## NAS (Synology) — long-term
- rsync `~/BEST-HQ` → NAS **ทุกคืน** · เก็บ snapshot รายเดือน
- HR/PDPA → share เข้ารหัส สิทธิ์จำกัด
- (สคริปต์ NAS sync จะสร้างหลังอนุมัติ)

## ลำดับ
1. `best_audit.sh` → รู้ขนาด/ของ sensitive
2. `best_backup.sh` (DRY-RUN → EXECUTE) → มี snapshot
3. ค่อยพิจารณา reorg (script สร้างหลังอนุมัติ)
