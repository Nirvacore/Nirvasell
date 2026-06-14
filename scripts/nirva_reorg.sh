#!/usr/bin/env bash
# NIRVA LIFE OS — Phase 3C MOVE (รันบน MacBook) · ปลายทาง = ~/HQ (ตาม HQ_BLUEPRINT.md)
# กฎ: ย้ายหลังอนุมัติ · backup ก่อน · ไม่ลบ · ไม่ทับ · ไม่แตะ git history · ไม่เปลี่ยน remote
#
# ลำดับปลอดภัย:
#   1) EXECUTE=1 bash hq_init.sh              # สร้างโครง ~/HQ
#   2) EXECUTE=1 bash nirva_backup.sh         # backup ก่อน (บังคับ)
#   3) bash nirva_reorg.sh                     # DRY-RUN ดูแผน
#   4) EXECUTE=1 bash nirva_reorg.sh           # ย้ายจริง (หลังอนุมัติ)
set -u
HQ="$HOME/HQ"; EXECUTE="${EXECUTE:-0}"; SKIP_BACKUP_CHECK="${SKIP_BACKUP_CHECK:-0}"

# "src|dest(relative ใน HQ)"
MAP=(
  "$HOME/nirvacore|01_CORE/NirvaCore"
  "$HOME/NIRVA|05_WORKSPACE/Review/NIRVA"                       # workspace รวม — ต้องแยกย่อยภายหลัง
  "$HOME/nirvawealth|02_PRODUCTS/NirvaWealth/source"           # ⚠️ no remote — backup+push ก่อน
  "$HOME/mu-tea|03_VENTURES/MuTea/source"
  "$HOME/Claude|04_KNOWLEDGE/Documentation/Claude"
  "$HOME/Doc.for.ERP|04_KNOWLEDGE/Documentation/Doc.for.ERP"
  "$HOME/nirva-archive|06_ARCHIVE/Legacy/nirva-archive"
  "$HOME/Downloads/nirva deploy|02_PRODUCTS/NirvaDeploy/source"
  "$HOME/Downloads/nirva-landing|02_PRODUCTS/NirvaDeploy/landing"
  "$HOME/Downloads/deploy|05_WORKSPACE/Review/deploy"          # ไม่ชัด — พักรอ review
  "$HOME/Downloads/nirva_deploy.zip|07_BACKUPS/Releases/nirva_deploy.zip"
  "$HOME/Downloads/NirvaGovTH Dev Spec.docx|04_KNOWLEDGE/Documentation/NirvaGov/NirvaGovTH Dev Spec.docx"
  "$HOME/Documents/Claude|04_KNOWLEDGE/Documentation/Claude-Documents"   # แยกชื่อ ไม่ merge
  "$HOME/Documents/VCode|05_WORKSPACE/Review/VCode"
)
for b in "$HOME"/nirva-backup-*; do
  [ -e "$b" ] && MAP+=("$b|07_BACKUPS/Releases/$(basename "$b")")
done

run() { echo "  \$ $*"; [ "$EXECUTE" = "1" ] && eval "$@"; }
echo "# NIRVA REORG → ~/HQ — mode: $([ "$EXECUTE" = 1 ] && echo EXECUTE || echo DRY-RUN)"

# safety gate: ต้องมี backup ก่อน
if [ "$SKIP_BACKUP_CHECK" != "1" ]; then
  if [ -z "$(find "$HQ/07_BACKUPS" -type f 2>/dev/null | head -1)" ]; then
    echo "❌ ยังไม่พบ backup ใน $HQ/07_BACKUPS — รัน 'EXECUTE=1 bash nirva_backup.sh' ก่อน (หรือ SKIP_BACKUP_CHECK=1)"
    exit 1
  fi
fi

for entry in "${MAP[@]}"; do
  src="${entry%%|*}"; rel="${entry##*|}"; dst="$HQ/$rel"
  echo "--- ${src}  →  ${dst}"
  [ -e "$src" ] || { echo "  absent (ข้าม)"; continue; }

  # ปลายทาง: ถ้ามีอยู่และไม่ว่าง = หยุด (ไม่ทับ) ; ถ้าเป็นโฟลเดอร์ว่าง (จาก hq_init) = ลบทิ้งปลอดภัยแล้วย้าย
  if [ -e "$dst" ]; then
    if [ -d "$dst" ] && [ -z "$(ls -A "$dst" 2>/dev/null)" ]; then
      run "rmdir \"$dst\""        # rmdir = ลบเฉพาะโฟลเดอร์ว่าง (ปลอดภัย ข้อมูลไม่หาย)
    else
      echo "  ⚠️ ปลายทางมีอยู่และไม่ว่าง — หยุด ไม่ทับ (ตรวจเอง)"; continue
    fi
  fi
  run "mkdir -p \"$(dirname "$dst")\""

  # หัวใจ: verify remote/branch ก่อนย้าย
  if [ "$src" = "$HOME/nirvacore" ]; then
    ro=$(git -C "$src" config --get remote.origin.url 2>/dev/null); br=$(git -C "$src" rev-parse --abbrev-ref HEAD 2>/dev/null)
    echo "  ตรวจหัวใจ: remote=$ro branch=$br"
    case "$ro" in *nirvacore-v1*) : ;; *) echo "  ⚠️ remote ไม่ตรง nirvacore-v1 — ข้าม (ตรวจเอง)"; continue;; esac
  fi
  run "mv \"$src\" \"$dst\""
done

echo
echo "# เสร็จ ($([ "$EXECUTE" = 1 ] && echo 'ย้ายจริงแล้ว' || echo 'DRY-RUN — ยังไม่ย้าย'))"
echo "# nirvawealth ไม่มี remote → สร้าง repo + push ก่อน (ขั้นแยก)"
echo "# 05_WORKSPACE/Review/{NIRVA,deploy,VCode} = ต้องแยกย่อยไปบ้านจริงภายหลัง"
