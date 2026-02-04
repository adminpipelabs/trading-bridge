#!/bin/bash
# Quick Migration Script
# Uses Railway CLI to run migrations

set -e

echo "=========================================="
echo "Running Database Migrations via Railway"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# Method 1: Use railway connect postgres
echo "🔗 Connecting to Railway PostgreSQL..."
echo ""

# Read SQL file and execute via Railway
if command -v railway &> /dev/null; then
    echo "📋 Executing migrations..."
    cat migrations/COMPLETE_SETUP.sql | railway connect postgres 2>&1 | tee migration_output.log
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo ""
        echo "✅ Migrations completed!"
        echo ""
        echo "Verifying..."
        echo "SELECT column_name FROM information_schema.columns WHERE table_name = 'bots' AND column_name = 'health_status';" | railway connect postgres 2>&1 | grep -q "health_status" && echo "✅ health_status column exists" || echo "⚠️  health_status column check failed"
        echo "SELECT table_name FROM information_schema.tables WHERE table_name = 'trading_keys';" | railway connect postgres 2>&1 | grep -q "trading_keys" && echo "✅ trading_keys table exists" || echo "⚠️  trading_keys table check failed"
    else
        echo ""
        echo "❌ Migration failed. Check migration_output.log for details."
        exit 1
    fi
else
    echo "❌ Railway CLI not found"
    echo "   Install: npm i -g @railway/cli"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Migration Complete!"
echo "=========================================="
