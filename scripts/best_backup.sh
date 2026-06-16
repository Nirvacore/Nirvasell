#!/usr/bin/env bash
# BEST GROUP Back Office — BACKUP · รันบน Mac
#   BEST_ROOT=/path/to/BEST bash best_backup.sh           # DRY-RUN
#   EXECUTE=1 BEST_ROOT=/path/to/BEST bash best_backup.sh # ทำจริง
# กฎ: ไม่ลบ ไม่ทับ ไม่แตะ git history · HR/PDPA ห้ามขึ้น cloud
set -u
ROOT="${BEST_ROOT:-$HOME}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$HOME/BEST-HQ/99_BACKUP/Daily/$STAMP"
EXECUTE="${EXECUTE:-0}"
run() { echo "  \$ $*"; [ "$EXECUTE" = "1" ] && eval "$@"; }

# โฟลเดอร์ back office (ปรับให้ตรงของจริงหลัง best_audit.sh)
FOLDERS=(ERP 2Store 4Document 5Operation 6Job 7Marketing 8Car Backup MAC)

echo "# BEST BACKUP — $STAMP — mode: $([ "$EXECUTE" = 1 ] && echo EXECUTE || echo DRY-RUN) — root: $ROOT"
run "mkdir -p \"$DEST\""
for f in "${FOLDERS[@]}"; do
  src="$ROOT/$f"
  [ -e "$src" ] || { echo "absent (ข้าม): $src"; continue; }
  echo "--- backup: $src"
  run "tar -czf \"$DEST/${f// /_}.tar.gz\" -C \"$ROOT\" \"$f\""
done
echo "# หมายเหตุ: NIRVAPROCURE = ของ NIRVA-HQ ไม่ backup ที่นี่ (separation policy)"
echo "# ⚠️ ถ้ามีโฟลเดอร์ HR/PDPA → เก็บ backup ในดิสก์เข้ารหัส/NAS เท่านั้น ห้ามขึ้น cloud"
echo "# เสร็จ ($([ "$EXECUTE" = 1 ] && echo 'จริง' || echo 'DRY-RUN'))"
