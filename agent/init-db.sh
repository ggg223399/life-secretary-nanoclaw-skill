#!/bin/bash
# life-secretary database initializer + migration runner
# Usage: bash init-db.sh [DB_PATH]
# Default DB_PATH: /workspace/group/life-secretary.db

set -e

DB_PATH="${1:-/workspace/group/life-secretary.db}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCHEMA="$SCRIPT_DIR/schema.sql"
MIGRATIONS_DIR="$SCRIPT_DIR/migrations"
LATEST_VERSION=1

# ── helpers ───────────────────────────────────────────────────────────────────

db() { "$SCRIPT_DIR/sqlite3" "$DB_PATH" "$@"; }

has_settings_table() {
  db "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='settings';" 2>/dev/null || echo "0"
}

get_version() {
  db "SELECT value FROM settings WHERE key='schema_version';" 2>/dev/null || echo "0"
}

ensure_settings_table() {
  db "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);"
}

set_version() {
  ensure_settings_table
  db "INSERT OR REPLACE INTO settings(key,value,updated_at) VALUES('schema_version','$1',datetime('now'));"
}

backup() {
  local v="$1"
  local bak="${DB_PATH}.bak-v${v}"
  cp "$DB_PATH" "$bak"
  echo "  Backup saved: $bak"
}

# ── fresh install ─────────────────────────────────────────────────────────────

if [ ! -f "$DB_PATH" ]; then
  echo "Fresh install — creating database at: $DB_PATH"
  mkdir -p "$(dirname "$DB_PATH")"
  db < "$SCHEMA"
  set_version "$LATEST_VERSION"
  echo "Database created at schema v${LATEST_VERSION}."
  db ".tables"
  exit 0
fi

# ── existing DB: check version ────────────────────────────────────────────────

HAS_SETTINGS=$(has_settings_table)
if [ "$HAS_SETTINGS" = "0" ]; then
  CURRENT_VERSION=0
else
  CURRENT_VERSION=$(get_version)
  [ -z "$CURRENT_VERSION" ] && CURRENT_VERSION=0
fi

if [ "$CURRENT_VERSION" -ge "$LATEST_VERSION" ]; then
  echo "Database is up to date (v${CURRENT_VERSION}). Nothing to do."
  exit 0
fi

echo "Database needs migration: v${CURRENT_VERSION} → v${LATEST_VERSION}"

# ── run migrations ────────────────────────────────────────────────────────────

for migration in $(ls "$MIGRATIONS_DIR"/*.sql 2>/dev/null | sort); do
  filename="$(basename "$migration")"
  migration_version="${filename%%.*}"
  migration_version="${migration_version#0}"   # strip leading zeros

  if [ "$migration_version" -le "$CURRENT_VERSION" ]; then
    continue
  fi

  echo "  Applying migration $filename ..."
  backup "$CURRENT_VERSION"
  db < "$migration"
  set_version "$migration_version"
  CURRENT_VERSION="$migration_version"
  echo "  Migration $filename applied. Now at v${CURRENT_VERSION}."
done

echo "Migration complete. Database is now at v${CURRENT_VERSION}."
db ".tables"
