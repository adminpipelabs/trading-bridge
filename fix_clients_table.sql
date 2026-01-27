-- Quick Fix: Add missing columns to clients table
-- Run this in Railway PostgreSQL Query Console

ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(100);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_type VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS tier VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'client';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- Verify columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'clients'
ORDER BY ordinal_position;
