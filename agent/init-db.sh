#!/bin/bash
# Initialize life-secretary SQLite database
# Usage: bash init-db.sh [DB_PATH]
# Default DB_PATH: /workspace/group/life-secretary.db

DB_PATH="${1:-/workspace/group/life-secretary.db}"
SCRIPT_DIR="$(dirname "$0")"

echo "Initializing database at: $DB_PATH"
sqlite3 "$DB_PATH" < "$SCRIPT_DIR/schema.sql"
echo "Database initialized successfully."
sqlite3 "$DB_PATH" ".tables"
