#!/bin/bash
# Run database migrations via Railway CLI
# This script attempts to connect to Railway PostgreSQL and run migrations

set -e

echo "🚀 Running database migrations..."
echo ""

# Get DATABASE_URL from Railway
echo "📡 Getting DATABASE_URL from Railway..."
DB_URL=$(railway variables --json 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin).get('DATABASE_URL', ''))" 2>/dev/null || railway variables 2>&1 | grep "DATABASE_URL" | head -1 | awk '{print $2}')

if [ -z "$DB_URL" ]; then
    echo "❌ Could not get DATABASE_URL from Railway"
    echo ""
    echo "Please run the migration manually:"
    echo "1. Go to Railway Dashboard → PostgreSQL → Query tab"
    echo "2. Copy/paste contents of migrations/run_all_migrations.sql"
    echo "3. Execute"
    exit 1
fi

# Check if it's an internal URL (won't work from local machine)
if [[ "$DB_URL" == *"railway.internal"* ]]; then
    echo "⚠️  Found internal Railway URL (won't work from local machine)"
    echo ""
    echo "Please use Railway Dashboard Query tab instead:"
    echo "1. Go to Railway Dashboard → PostgreSQL → Query tab"
    echo "2. Copy/paste contents of migrations/run_all_migrations.sql"
    echo "3. Execute"
    exit 1
fi

# Try to run migration with psql
echo "✅ Found DATABASE_URL"
echo "📝 Running migrations..."

if command -v psql &> /dev/null; then
    psql "$DB_URL" -f migrations/run_all_migrations.sql
    echo ""
    echo "✅ Migration completed!"
    echo ""
    echo "Verifying..."
    psql "$DB_URL" -f migrations/verify_migrations.sql
else
    echo "❌ psql not found. Please install PostgreSQL client or use Railway Dashboard Query tab"
    exit 1
fi
