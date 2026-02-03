#!/bin/bash
# Run database migrations via Docker PostgreSQL client
# This connects to Railway PostgreSQL and runs migrations

set -e

echo "🐳 Running database migrations via Docker..."
echo ""

# Get DATABASE_URL from Railway
echo "📡 Getting DATABASE_URL from Railway..."
DB_URL=$(railway variables --json 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin).get('DATABASE_URL', ''))" 2>/dev/null || railway variables 2>&1 | grep "DATABASE_URL" | head -1 | awk -F'=' '{print $2}' | tr -d ' ')

if [ -z "$DB_URL" ]; then
    echo "❌ Could not get DATABASE_URL from Railway"
    echo ""
    echo "Please provide DATABASE_URL manually:"
    echo "  export DATABASE_URL='your-connection-string'"
    echo "  ./scripts/run_migration_docker.sh"
    exit 1
fi

# Check if it's an internal URL - we need to convert it or get public URL
if [[ "$DB_URL" == *"railway.internal"* ]]; then
    echo "⚠️  Found internal Railway URL"
    echo ""
    echo "We need the PUBLIC connection string. Options:"
    echo ""
    echo "Option 1: Get public URL from Railway Dashboard:"
    echo "  1. Go to Railway Dashboard → PostgreSQL → Connect"
    echo "  2. Select 'Public Network'"
    echo "  3. Copy the connection string"
    echo "  4. Run: export DATABASE_URL='your-public-url' && ./scripts/run_migration_docker.sh"
    echo ""
    echo "Option 2: Use Railway Query tab (easiest):"
    echo "  1. Go to Railway Dashboard → PostgreSQL → Query tab"
    echo "  2. Copy/paste contents of migrations/run_all_migrations.sql"
    echo ""
    exit 1
fi

echo "✅ Found DATABASE_URL"
echo "🐳 Using Docker PostgreSQL client..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Run migration using postgres Docker image
echo "📝 Running migrations..."
docker run --rm -i \
    -e PGPASSWORD=$(echo "$DB_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p') \
    postgres:15-alpine \
    psql "$DB_URL" < migrations/run_all_migrations.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration completed successfully!"
    echo ""
    echo "🔍 Verifying migration..."
    docker run --rm -i \
        -e PGPASSWORD=$(echo "$DB_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p') \
        postgres:15-alpine \
        psql "$DB_URL" < migrations/verify_migrations.sql
else
    echo ""
    echo "❌ Migration failed. Check the error above."
    exit 1
fi
