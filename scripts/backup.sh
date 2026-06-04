#!/usr/bin/env bash
# Snapshot every per-user DB + the operator/admin settings into a single
# timestamped tarball. Designed for cron on the Docker host (NOT inside
# the container — we want filesystem-level backups outside the running app).
#
#   crontab -e
#   0 3 * * * /home/deploy/nirva.sell/scripts/backup.sh
#
# Retains 14 days by default; set BACKUP_KEEP_DAYS to change.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${ROOT}/data"
BACKUP_DIR="${BACKUP_DIR:-${ROOT}/backups}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"

if [[ ! -d "${DATA_DIR}" ]]; then
    echo "ERR: ${DATA_DIR} not found" >&2
    exit 1
fi

mkdir -p "${BACKUP_DIR}"

STAMP="$(date -u +%Y%m%d-%H%M%SZ)"
OUT="${BACKUP_DIR}/nirva-${STAMP}.tgz"

# Use --checkpoint so cron emails show progress on big DBs.
tar --create --gzip --checkpoint=1000 --checkpoint-action=dot \
    -f "${OUT}" -C "${DATA_DIR}" . \
    && echo "OK ${OUT} ($(du -h "${OUT}" | cut -f1))"

# Prune old backups
find "${BACKUP_DIR}" -name 'nirva-*.tgz' -mtime "+${KEEP_DAYS}" -delete

# If TELEGRAM_BOT_TOKEN + TELEGRAM_DEFAULT_CHAT_ID are set in env,
# send a notification. (Sourcing .env is optional.)
if [[ -f "${ROOT}/.env" ]]; then
    set -a; . "${ROOT}/.env"; set +a
fi

if [[ -n "${TELEGRAM_BOT_TOKEN:-}" && -n "${TELEGRAM_DEFAULT_CHAT_ID:-}" ]]; then
    SIZE="$(du -h "${OUT}" | cut -f1)"
    MSG="✅ nirva backup ${STAMP} (${SIZE})"
    curl -fsS -X POST \
        "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${TELEGRAM_DEFAULT_CHAT_ID}" \
        --data-urlencode "text=${MSG}" >/dev/null \
        || echo "WARN: telegram notify failed" >&2
fi
