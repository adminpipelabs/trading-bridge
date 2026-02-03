#!/bin/bash
# Alternative: Use Railway CLI connect with SQL file
# This uses Railway's internal connection which should work

set -e

echo "🚀 Running migration via Railway CLI..."
echo ""

# Create a temporary SQL file with the migration
SQL_FILE="/tmp/railway_migration_$$.sql"
cat migrations/run_all_migrations.sql > "$SQL_FILE"

echo "📝 Migration SQL prepared"
echo ""
echo "⚠️  Railway CLI 'connect' opens an interactive session."
echo ""
echo "Please run this manually:"
echo ""
echo "  1. railway connect postgres"
echo "  2. Once connected, run: \\i $SQL_FILE"
echo "  3. Or copy/paste the SQL from migrations/run_all_migrations.sql"
echo ""
echo "OR use Railway Dashboard Query tab (easiest):"
echo "  1. Go to Railway Dashboard → PostgreSQL → Query tab"
echo "  2. Copy/paste contents of migrations/run_all_migrations.sql"
echo "  3. Execute"
echo ""

# Cleanup
trap "rm -f $SQL_FILE" EXIT
