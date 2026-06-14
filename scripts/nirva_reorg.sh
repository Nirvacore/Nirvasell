#!/usr/bin/env bash
# NIRVA Phase 3C — EXECUTION PLAN / MOVE (รันบน MacBook)
# กฎ: ย้ายหลังอนุมัติ · backup ก่อน · ไม่ลบ · ไม่ทับ · ไม่แตะ git history · ไม่เปลี่ยนชื่อ remote
#
# ลำดับที่ปลอดภัย:
#   1) EXECUTE=1 bash nirva_backup.sh        # สร้าง backup ก่อน (บังคับ)
#   2) bash nirva_reorg.sh                    # DRY-RUN: ดูแผนย้าย (ไม่ทำจริง)
#   3) EXECUTE=1 bash nirva_reorg.sh          # ทำจริง (หลังคุณอนุมัติ)
#
# กลไกกันพลาด:
#   - ต้องมี backup ใน ~/NIRVA-HQ/07-Backups/ ก่อน ไม่งั้น refuse (เว้นแต่ SKIP_BACKUP_CHECK=1)
#   - ถ้าปลายทางมีอยู่แล้ว = หยุด (ไม่ทับ)
#   - ใช้ mv (ย้าย ไม่ทำสำเนาซ้ำ) — ต้นทาง+ปลายทางบน volume เดียว
#   - nirvacore: ตรวจ remote=nirvacore-v1 / branch=main ก่อน ไม่งั้นเตือนและข้าม

set -u
HQ="$HOME/NIRVA-HQ"
EXECUTE="${EXECUTE:-0}"
SKIP_BACKUP_CHECK="${SKIP_BACKUP_CHECK:-0}"

# "src|dest(relative ใน HQ)"  — ตาม MAC_REORGANIZATION_PLAN.md
MAP=(
  "$HOME/nirvacore|01-Core/nirvacore"
  "$HOME/NIRVA|05-Workspace/NIRVA"
  "$HOME/nirvawealth|03-Ventures/nirvawealth"
  "$HOME/mu-tea|03-Ventures/mu-tea"
  "$HOME/Claude|04-Knowledge/Claude"
  "$HOME/Doc.for.ERP|04-Knowledge/Doc.for.ERP"
  "$HOME/nirva-archive|06-Archive/nirva-archive"
  "$HOME/Downloads/nirva deploy|02-Products/nirva-deploy"
  "$HOME/Downloads/nirva-landing|02-Products/nirva-landing"
  "$HOME/Downloads/deploy|06-Archive/deploy-review"
  "$HOME/Downloads/nirva_deploy.zip|07-Backups/nirva_deploy.zip"
  "$HOME/Downloads/NirvaGovTH Dev Spec.docx|04-Knowledge/NirvaGov/NirvaGovTH Dev Spec.docx"
  "$HOME/Documents/Claude|04-Knowledge/Claude-Documents"
  "$HOME/Documents/VCode|05-Workspace/VCode"
)
# nirva-backup-* (glob แยก เพราะมีหลายตัว)
for b in "$HOME"/nirva-backup-*; do
  [ -e "$b" ] && MAP+=("$b|07-Backups/$(basename "$b")")
done

run() { echo "  \$ $*"; [ "$EXECUTE" = "1" ] && eval "$@"; }

echo "# NIRVA REORG — mode: $([ "$EXECUTE" = 1 ] && echo EXECUTE || echo DRY-RUN)"

# --- safety gate: ต้องมี backup ก่อน ---
if [ "$SKIP_BACKUP_CHECK" != "1" ]; then
  if [ ! -d "$HQ/07-Backups" ] || [ -z "$(ls -A "$HQ/07-Backups" 2>/dev/null)" ]; then
    echo "❌ ยังไม่พบ backup ใน $HQ/07-Backups — รัน 'EXECUTE=1 bash nirva_backup.sh' ก่อน"
    echo "   (ถ้ายืนยันว่ามี backup ที่อื่นแล้ว: SKIP_BACKUP_CHECK=1)"
    exit 1
  fi
fi

# --- สร้างโครง HQ ---
for d in 01-Core 02-Products 03-Ventures 04-Knowledge 05-Workspace 06-Archive 07-Backups 04-Knowledge/NirvaGov; do
  run "mkdir -p \"$HQ/$d\""
done

for entry in "${MAP[@]}"; do
  src="${entry%%|*}"; rel="${entry##*|}"; dst="$HQ/$rel"
  echo "--- ${src}  →  ${dst}"
  [ -e "$src" ] || { echo "  absent (ข้าม)"; continue; }
  [ -e "$dst" ] && { echo "  ⚠️ ปลายทางมีอยู่แล้ว — หยุด ไม่ทับ (ตรวจเอง)"; continue; }

  # nirvacore: verify remote/branch ก่อนย้ายหัวใจ
  if [ "$src" = "$HOME/nirvacore" ]; then
    ro=$(git -C "$src" config --get remote.origin.url 2>/dev/null)
    br=$(git -C "$src" rev-parse --abbrev-ref HEAD 2>/dev/null)
    echo "  ตรวจหัวใจ: remote=$ro branch=$br"
    case "$ro" in
      *Nirvacore/nirvacore-v1*|*nirvacore-v1*) : ;;
      *) echo "  ⚠️ remote ไม่ตรง nirvacore-v1 — ข้ามเพื่อความปลอดภัย (ตรวจเอง)"; continue ;;
    esac
  fi
  run "mv \"$src\" \"$dst\""
done

echo
echo "# เสร็จ ($([ "$EXECUTE" = 1 ] && echo 'ย้ายจริงแล้ว' || echo 'DRY-RUN — ยังไม่ย้าย'))"
echo "# ต้นทางเดิมไม่ถูกลบเพิ่มเติม — ข้อมูลอยู่ที่ปลายทาง + backup tar"
echo "# nirvawealth ไม่มี remote → แนะนำสร้าง repo แล้ว push (ทำแยก ขั้นถัดไป)"
