#!/bin/bash
# Simple Docker migration runner
# Usage: DATABASE_URL='your-public-url' ./scripts/run_migration_docker_simple.sh

set -e

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set"
    echo ""
    echo "Usage:"
    echo "  DATABASE_URL='postgresql://user:pass@host:port/db' ./scripts/run_migration_docker_simple.sh"
    echo ""
    echo "To get public DATABASE_URL from Railway:"
    echo "  1. Go to Railway Dashboard → PostgreSQL → Connect"
    echo "  2. Select 'Public Network'"
    echo "  3. Copy the connection string"
    exit 1
fi

echo "🐳 Running migrations via Docker..."
echo ""

# Extract password for PGPASSWORD env var
PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')

# Run migration
docker run --rm -i \
    -e PGPASSWORD="$PGPASSWORD" \
    postgres:15-alpine \
    psql "$DATABASE_URL" < migrations/run_all_migrations.sql

echo ""
echo "✅ Migration completed!"
echo ""
echo "🔍 Verifying..."
docker run --rm -i \
    -e PGPASSWORD="$PGPASSWORD" \
    postgres:15-alpine \
    psql "$DATABASE_URL" < migrations/verify_migrations.sql
