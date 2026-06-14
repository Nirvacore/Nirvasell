#!/usr/bin/env bash
# NIRVA LIFE OS — สร้างโครง ~/HQ ทั้งหมด (ว่างเปล่า) ตาม HQ_BLUEPRINT.md
# รันบน MacBook · ปลอดภัย (สร้างโฟลเดอร์ว่างเท่านั้น ไม่ย้าย/ไม่ลบ)
# default = DRY-RUN ;  ทำจริง:  EXECUTE=1 bash hq_init.sh
set -u
HQ="$HOME/HQ"; EXECUTE="${EXECUTE:-0}"
run() { echo "  \$ $*"; [ "$EXECUTE" = "1" ] && eval "$@"; }

DIRS=(
  "01_CORE/NirvaCore"
  "02_PRODUCTS/NirvaDeploy" "02_PRODUCTS/NirvaProcure" "02_PRODUCTS/NirvaWealth"
  "02_PRODUCTS/NirvaGov" "02_PRODUCTS/NirvaMedia" "02_PRODUCTS/NirvaAcademy"
  "03_VENTURES/MuVerse" "03_VENTURES/MuTea" "03_VENTURES/Soul" "03_VENTURES/Nova"
  "04_KNOWLEDGE/ISO" "04_KNOWLEDGE/Research" "04_KNOWLEDGE/Prompts"
  "04_KNOWLEDGE/NotebookLM" "04_KNOWLEDGE/Documentation"
  "05_WORKSPACE/Inbox" "05_WORKSPACE/Review" "05_WORKSPACE/This_Week" "05_WORKSPACE/Waiting"
  "06_ARCHIVE/2025" "06_ARCHIVE/2026" "06_ARCHIVE/Legacy" "06_ARCHIVE/Retired"
  "07_BACKUPS/Daily" "07_BACKUPS/Weekly" "07_BACKUPS/Monthly" "07_BACKUPS/Releases"
  "08_MEDIA/Photos" "08_MEDIA/Video" "08_MEDIA/Audio" "08_MEDIA/Graphics" "08_MEDIA/Brands"
  "09_PERSONAL/Family" "09_PERSONAL/Health" "09_PERSONAL/Finance" "09_PERSONAL/Travel" "09_PERSONAL/Learning"
  "10_SYSTEM/Installers" "10_SYSTEM/SDKs" "10_SYSTEM/Scripts" "10_SYSTEM/Configs"
)
echo "# HQ INIT — mode: $([ "$EXECUTE" = 1 ] && echo EXECUTE || echo DRY-RUN) — root: $HQ"
for d in "${DIRS[@]}"; do run "mkdir -p \"$HQ/$d\""; done
# กันเผลอ commit โครงว่างขึ้น cloud / มี marker README ในแต่ละหมวด
run "printf 'See HQ_BLUEPRINT.md\\n' > \"$HQ/README.txt\""
echo "# เสร็จ ($([ "$EXECUTE" = 1 ] && echo 'สร้างจริงแล้ว' || echo 'DRY-RUN'))"
