#!/bin/bash
# Backup script for PostgreSQL database
# Usage: ./scripts/backup_postgres.sh [backup_dir]

BACKUP_DIR=${1:-.}
DB_NAME=${POSTGRES_DB:-trading_db}
DB_USER=${POSTGRES_USER:-postgres}
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5432}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/trading_db_backup_$TIMESTAMP.sql"

echo "Starting backup of $DB_NAME..."
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v -f "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup completed: $BACKUP_FILE"
    # Optionally compress
    gzip "$BACKUP_FILE"
    echo "Compressed: ${BACKUP_FILE}.gz"
else
    echo "Backup failed!"
    exit 1
fi
