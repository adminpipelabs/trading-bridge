#!/bin/bash
# Simple script to run database migrations
# Uses Railway CLI or DATABASE_URL environment variable

set -e

echo "=========================================="
echo "Database Migration Runner"
echo "=========================================="
echo ""

SQL_FILE="migrations/COMPLETE_SETUP.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Migration file not found: $SQL_FILE"
    exit 1
fi

# Method 1: Use Railway CLI (if linked to project)
if command -v railway &> /dev/null; then
    echo "🔍 Trying Railway CLI method..."
    if railway run psql < "$SQL_FILE" 2>/dev/null; then
        echo ""
        echo "✅ Migrations completed via Railway CLI!"
        exit 0
    fi
    echo "⚠️  Railway CLI method failed, trying Python..."
fi

# Method 2: Use Python script (works with DATABASE_URL)
echo "🐍 Running Python migration script..."
python3 scripts/run_migrations.py
