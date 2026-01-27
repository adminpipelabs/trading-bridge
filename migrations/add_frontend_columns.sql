-- Migration: Add frontend-compatible columns to clients table
-- Date: 2026-01-27
-- Purpose: Add columns expected by Pipe Labs backend (backend-pipelabs-dashboard)

-- Add missing columns (IF NOT EXISTS prevents errors if columns already exist)
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(100);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_type VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS tier VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'client';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}';

-- Add indexes for commonly queried columns
CREATE INDEX IF NOT EXISTS idx_clients_wallet_address ON clients(wallet_address);
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);

-- Verify columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'clients'
ORDER BY ordinal_position;
