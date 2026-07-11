#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <backup-file>"
  exit 1
fi

BACKUP_FILE="$1"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WEB_DIR="${ROOT_DIR}/web"
DB_ENGINE="${DB_ENGINE:-django.db.backends.sqlite3}"

if [[ ! -f "${BACKUP_FILE}" ]]; then
  echo "Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

if [[ "${DB_ENGINE}" == *"postgres"* ]]; then
  : "${DB_NAME:?DB_NAME is required for postgres restore}"
  gunzip -c "${BACKUP_FILE}" | psql "${DB_NAME}"
  echo "Postgres restore complete."
else
  SQLITE_PATH="${DB_NAME:-${WEB_DIR}/db.sqlite3}"
  cp "${BACKUP_FILE}" "${SQLITE_PATH}"
  echo "SQLite restore complete."
fi
