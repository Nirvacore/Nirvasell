#!/usr/bin/env bash
# NIRVA Phase 3B — BACKUP (รันบน MacBook)
# กฎ: Backup ก่อนย้ายเสมอ · ไม่ลบ · ไม่ทับ · ไม่แตะ git history
#
# ค่าเริ่มต้น = DRY-RUN (พิมพ์คำสั่งเฉยๆ ไม่ทำจริง)
# จะทำจริงต้องสั่ง:  EXECUTE=1 bash nirva_backup.sh
#
# ผลลัพธ์: snapshot .tar.gz ของทุกโฟลเดอร์เป้าหมาย ไปไว้ใน ~/NIRVA-HQ/07-Backups/<วันที่>/

set -u
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$HOME/NIRVA-HQ/07-Backups/$STAMP"
EXECUTE="${EXECUTE:-0}"

# โฟลเดอร์ที่ต้อง backup (ตาม MAC_REORGANIZATION_PLAN.md)
SOURCES=(
  "$HOME/nirvacore"
  "$HOME/NIRVA"
  "$HOME/nirvawealth"
  "$HOME/mu-tea"
  "$HOME/Claude"
  "$HOME/Doc.for.ERP"
  "$HOME/nirva-archive"
  "$HOME/Downloads/nirva deploy"
  "$HOME/Downloads/nirva-landing"
  "$HOME/Downloads/deploy"
  "$HOME/Documents/Claude"
  "$HOME/Documents/VCode"
)

run() {  # พิมพ์คำสั่งเสมอ; ทำจริงเฉพาะเมื่อ EXECUTE=1
  echo "  \$ $*"
  [ "$EXECUTE" = "1" ] && eval "$@"
}

echo "# NIRVA BACKUP — $STAMP — mode: $([ "$EXECUTE" = 1 ] && echo EXECUTE || echo DRY-RUN)"
echo "# ปลายทาง backup: $DEST"
run "mkdir -p \"$DEST\""

for src in "${SOURCES[@]}"; do
  if [ ! -e "$src" ]; then echo "absent (ข้าม): $src"; continue; fi
  base="$(basename "$src" | tr ' ' '_')"
  echo "--- backup: $src"
  # ถ้าเป็น git repo: บันทึกสถานะไว้ด้วย (read-only, ไม่แก้อะไร)
  if [ -d "$src/.git" ]; then
    echo "  (git repo) สถานะ — ไม่แตะ history:"
    echo "  \$ git -C \"$src\" status -s ; git -C \"$src\" log -1 --oneline ; git -C \"$src\" rev-list --left-right --count @{u}...HEAD 2>/dev/null"
    if [ "$EXECUTE" = "1" ]; then
      git -C "$src" status -s | sed 's/^/    /'
      git -C "$src" log -1 --oneline | sed 's/^/    last: /'
      git -C "$src" rev-list --left-right --count @{u}...HEAD 2>/dev/null | sed 's/^/    behind<->ahead: /' || echo "    (no upstream)"
    fi
  fi
  # tar snapshot (รวม node_modules ออกเพื่อลดขนาด — โค้ด/ประวัติ git ยังครบ)
  run "tar --exclude='node_modules' --exclude='.next' --exclude='dist' -czf \"$DEST/${base}.tar.gz\" -C \"$(dirname "$src")\" \"$(basename "$src")\""
done

echo
echo "# เสร็จ ($([ "$EXECUTE" = 1 ] && echo 'สร้าง backup จริงแล้ว' || echo 'DRY-RUN — ยังไม่สร้างจริง'))"
echo "# ตรวจ backup ก่อนไปขั้น 3C:  ls -lh \"$DEST\""
