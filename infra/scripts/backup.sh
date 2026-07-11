#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WEB_DIR="${ROOT_DIR}/web"
BACKUP_DIR="${ROOT_DIR}/temp/backups"
TS="$(date +%Y%m%d-%H%M%S)"

mkdir -p "${BACKUP_DIR}"

DB_ENGINE="${DB_ENGINE:-django.db.backends.sqlite3}"

if [[ "${DB_ENGINE}" == *"postgres"* ]]; then
  : "${DB_NAME:?DB_NAME is required for postgres backups}"
  OUT="${BACKUP_DIR}/drivesphere-db-${TS}.sql.gz"
  pg_dump --no-owner --no-privileges "${DB_NAME}" | gzip > "${OUT}"
  echo "Postgres backup created: ${OUT}"
else
  SQLITE_PATH="${DB_NAME:-${WEB_DIR}/db.sqlite3}"
  OUT="${BACKUP_DIR}/drivesphere-db-${TS}.sqlite3"
  cp "${SQLITE_PATH}" "${OUT}"
  echo "SQLite backup created: ${OUT}"
fi
