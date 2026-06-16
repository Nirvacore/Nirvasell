# LOCAL_REGISTRY.md — MacBook Local Inventory
> NIRVA MASTER COMMAND CENTER · Phase 2A (House Cleaning = discovery only) · 2026-06-14
> **No move / no rename / no merge / no delete / no git ops**

## แหล่งหลักฐาน & ข้อจำกัด (อ่านก่อน)
- **Source ของรายการนี้** = ผู้ใช้รายงานชื่อโฟลเดอร์ ("Evidence discovered") — *ยังไม่ได้เปิดไฟล์จริง*
- session รันบน **cloud VM** เข้า MacBook ไม่ได้ → field เชิงเทคนิค (last modified / .git / remote / branch / package.json / Docker / Prisma / README / node_modules) = **PENDING**
- ยืนยันทั้งหมดได้โดยรัน **`scripts/local_audit.sh`** บน Mac แล้วส่งผลกลับ
- ดังนั้น **Classification ทุกแถว = Confidence: Low** (provisional จากชื่อ)

Class: **A**=Production · **P**=Pending Verification · **B**=Product · **C**=Research/Knowledge · **D**=Archive/Backup

---

## A) Home (`~/`)
| Full path | Folder | Purpose (ประเมินจากชื่อ) | Tech fields | Match GitHub | Class* | Conf |
|---|---|---|---|---|---|---|
| `~/nirvacore` | nirvacore | **ผู้สมัครหัวใจ ERP** (working copy) | PENDING | `nirvacore-v1`? | **P** | Low |
| `~/NIRVA` | NIRVA | umbrella/workspace หรือ core อีกชุด — *ห้ามเดาว่าซ้ำ* | PENDING | ? | **P** | Low |
| `~/nirva-backup-*` | nirva-backup-* | สำรอง (ชื่อบอก backup) | PENDING | – | **D** | Low |
| `~/nirva-archive` | nirva-archive | เก็บถาวร (ชื่อบอก archive) | PENDING | – | **D** | Low |
| `~/nirvawealth` | nirvawealth | NirvaWealth — *ไม่มี repo บน GitHub* (orphan) | PENDING | **ไม่มี** | **C/B** | Low |
| `~/mu-tea` | mu-tea | Mu Tea (MUVERSE) local | PENDING | `MUTEA` | **C** | Low |
| `~/Claude` | Claude | artifacts/decisions/เอกสาร (Decision Truth) | PENDING | – | **C** | Low |
| `~/Doc.for.ERP` | Doc.for.ERP | เอกสารประกอบ ERP (knowledge) | PENDING | – | **C** | Low |

## B) Downloads (`~/Downloads/`) — ⚠️ ดู LOCAL_SOURCE_OF_TRUTH (HIGH RISK)
| Full path | Folder/File | Purpose (ประเมิน) | Tech fields | Match GitHub | Class* | Conf |
|---|---|---|---|---|---|---|
| `~/Downloads/nirva deploy` | nirva deploy | NirvaDeploy working copy | PENDING | `nirvadeploy`? | **P** | Low |
| `~/Downloads/nirva-landing` | nirva-landing | landing page | PENDING | ? | **B/C** | Low |
| `~/Downloads/deploy` | deploy | deploy artifact ทั่วไป | PENDING | ? | **? /D** | Low |
| `~/Downloads/nirva_deploy.zip` | nirva_deploy.zip | **archive zip** (snapshot) | (ไฟล์บีบอัด) | – | **D** | Low |
| `~/Downloads/NirvaGovTH Dev Spec.docx` | NirvaGovTH Dev Spec.docx | spec NirvaGov (knowledge) | (เอกสาร) | – | **C** | Low |
| `~/Downloads/other artifacts` | (อื่นๆ) | ไม่ทราบ | PENDING | – | **?** | Low |

## C) Documents (`~/Documents/`)
| Full path | Folder | Purpose (ประเมิน) | Tech fields | Match GitHub | Class* | Conf |
|---|---|---|---|---|---|---|
| `~/Documents/Claude` | Claude | เอกสาร/decisions (อาจซ้ำกับ `~/Claude`) | PENDING | – | **C** | Low |
| `~/Documents/VCode` | VCode | workspace VSCode/โค้ด | PENDING | ? | **?** | Low |

\* Class = ประเมินจากชื่อเท่านั้น — **ยกระดับ/ปรับเมื่อได้ผล `local_audit.sh`**

---

## ฟิลด์ที่ยังต้องเก็บ (สคริปต์เก็บให้ครบทุกตัวที่ Phase 2A สั่ง)
last modified · .git · remote origin · branch · package.json · Docker · Prisma · README · node_modules · ขนาด
→ รัน: `bash scripts/local_audit.sh > nirva_local_$(date +%Y%m%d).txt` แล้วส่งกลับ
