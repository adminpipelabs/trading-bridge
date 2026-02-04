#!/bin/bash
# Railway Migration Script
# Run PostgreSQL migrations using DATABASE_URL from Railway environment
# Execute with: railway run bash run_migrations.sh

set -e  # Exit on error

echo "============================================================"
echo "Railway PostgreSQL Migration Script"
echo "============================================================"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not found in environment"
    echo "   Make sure you're running this in Railway environment"
    exit 1
fi

echo "✅ DATABASE_URL found"
echo ""

# Extract database connection details
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')

echo "📋 Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo "👤 User: $DB_USER"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "📦 Installing PostgreSQL client..."
    apt-get update -qq && apt-get install -y -qq postgresql-client > /dev/null 2>&1 || {
        echo "⚠️  Could not install postgresql-client, trying with python..."
        python3 railway_migrate.py
        exit $?
    }
fi

# Read SQL file
SQL_FILE="migrations/COMPLETE_SETUP.sql"
if [ ! -f "$SQL_FILE" ]; then
    echo "❌ ERROR: Migration file not found: $SQL_FILE"
    exit 1
fi

echo "📄 SQL File: $SQL_FILE"
echo ""
echo "🔧 Executing migrations..."
echo ""

# Run migrations using psql
export PGPASSWORD="$DB_PASS"

# Execute SQL file
psql -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" -d "$DB_NAME" -f "$SQL_FILE" -v ON_ERROR_STOP=1

MIGRATION_EXIT=$?

if [ $MIGRATION_EXIT -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ Migrations completed successfully!"
    echo "============================================================"
    
    # Verify migrations
    echo ""
    echo "🔍 Verifying migrations..."
    echo ""
    
    psql -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            CASE WHEN EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'bots' AND column_name = 'health_status'
            ) THEN '✅ health_status column exists' 
            ELSE '❌ health_status column missing' END as health_status_check;
        
        SELECT 
            CASE WHEN EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'trading_keys'
            ) THEN '✅ trading_keys table exists' 
            ELSE '❌ trading_keys table missing' END as trading_keys_check;
        
        SELECT 
            CASE WHEN COUNT(*) = 0 THEN '✅ All clients have roles assigned' 
            ELSE '⚠️  ' || COUNT(*) || ' clients with NULL roles' END as roles_check
        FROM clients WHERE role IS NULL;
    "
    
    exit 0
else
    echo ""
    echo "============================================================"
    echo "❌ Migrations failed with exit code: $MIGRATION_EXIT"
    echo "============================================================"
    exit $MIGRATION_EXIT
fi
