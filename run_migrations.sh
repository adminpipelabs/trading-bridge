#!/bin/bash
# Run Database Migrations via Railway CLI
# This script executes the complete setup SQL

set -e

echo "=========================================="
echo "Running Database Migrations"
echo "=========================================="
echo ""

# Check if Railway CLI is available
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm i -g @railway/cli"
    exit 1
fi

# Check if linked to Railway project
if ! railway status &> /dev/null; then
    echo "⚠️  Not linked to Railway project. Linking now..."
    railway link
fi

echo "📋 Reading migration SQL..."
SQL_FILE="migrations/COMPLETE_SETUP.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Migration file not found: $SQL_FILE"
    exit 1
fi

echo "🔗 Connecting to Railway PostgreSQL..."
echo ""

# Try to run SQL via Railway CLI
# Railway CLI can execute SQL commands
railway run psql < "$SQL_FILE" 2>&1 || {
    echo ""
    echo "⚠️  Direct execution failed. Trying alternative method..."
    echo ""
    echo "Alternative: Get DATABASE_URL and run with psql"
    echo ""
    DATABASE_URL=$(railway variables get DATABASE_URL 2>/dev/null | grep -v "^$" | tail -1)
    
    if [ -z "$DATABASE_URL" ]; then
        echo "❌ Could not get DATABASE_URL from Railway"
        echo ""
        echo "Please run migrations manually:"
        echo "1. Railway Dashboard → PostgreSQL → Query tab"
        echo "2. Copy contents of: $SQL_FILE"
        echo "3. Paste and execute"
        exit 1
    fi
    
    echo "✅ Got DATABASE_URL"
    echo "🔧 Running migrations with psql..."
    echo "$DATABASE_URL" | sed 's|postgresql://|postgres://|' | xargs psql < "$SQL_FILE" 2>&1 || {
        echo ""
        echo "❌ Failed to run migrations"
        echo ""
        echo "Please run migrations manually:"
        echo "1. Railway Dashboard → PostgreSQL → Query tab"
        echo "2. Copy contents of: $SQL_FILE"
        echo "3. Paste and execute"
        exit 1
    }
}

echo ""
echo "✅ Migrations completed successfully!"
echo ""
echo "Verifying..."
railway run psql -c "SELECT id, name, account_identifier, role FROM clients LIMIT 5;" 2>/dev/null || echo "⚠️  Could not verify (this is OK if migrations succeeded)"

echo ""
echo "=========================================="
echo "✅ Database migrations complete!"
echo "=========================================="
