#!/bin/bash
# Quick Fix: Add missing columns to clients table
# Run this if you have psql installed and DATABASE_URL set

echo "🚀 Running SQL migration to add missing columns..."

# Get DATABASE_URL from Railway or environment
DATABASE_URL="${DATABASE_URL:-}"

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set"
    echo ""
    echo "Option 1: Set DATABASE_URL environment variable:"
    echo "  export DATABASE_URL='postgresql://postgres:PASSWORD@postgres.railway.internal:5432/railway'"
    echo ""
    echo "Option 2: Run SQL directly in Railway Dashboard:"
    echo "  1. Railway Dashboard → PostgreSQL → Data/Query tab"
    echo "  2. Copy SQL from fix_clients_table.sql"
    echo "  3. Paste and run"
    exit 1
fi

# Run SQL migration
psql "$DATABASE_URL" << EOF
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(100);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_type VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS tier VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'client';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- Verify
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'clients' 
ORDER BY ordinal_position;
EOF

echo ""
echo "✅ Migration complete!"
