#!/bin/bash
# backup.sh - Automated database backup script
# Run daily via cron or Railway scheduled job
# Usage: ./backup.sh

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/pipelabs_${TIMESTAMP}.sql.gz"

# Ensure DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Run backup
echo "📦 Starting backup at $(date)"
echo "   Database: $(echo $DATABASE_URL | sed 's/:[^:]*@/:***@/')"
echo "   Output: $BACKUP_FILE"

# Run pg_dump and compress
if pg_dump "$DATABASE_URL" | gzip > "$BACKUP_FILE"; then
    SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo "✅ Backup created successfully: $BACKUP_FILE ($SIZE)"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Delete old backups
echo "🧹 Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "pipelabs_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# List remaining backups
REMAINING=$(find "$BACKUP_DIR" -name "pipelabs_*.sql.gz" | wc -l)
echo "📊 Remaining backups: $REMAINING"
echo "✅ Backup complete at $(date)"
