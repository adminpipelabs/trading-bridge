-- ============================================
-- CREATE trading_keys TABLE IF MISSING
-- Run this in Railway PostgreSQL Query tab
-- ============================================

-- Check if table exists
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'trading_keys';

-- Create table if it doesn't exist
CREATE TABLE IF NOT EXISTS trading_keys (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) UNIQUE NOT NULL,
    encrypted_key TEXT NOT NULL,
    chain VARCHAR(20) DEFAULT 'solana',
    wallet_address VARCHAR(255),
    added_by VARCHAR(20) DEFAULT 'client',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_trading_keys_client_id ON trading_keys(client_id);
CREATE INDEX IF NOT EXISTS idx_trading_keys_wallet_address ON trading_keys(wallet_address);

-- Add columns if table exists but columns are missing
ALTER TABLE trading_keys 
ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(255),
ADD COLUMN IF NOT EXISTS added_by VARCHAR(20) DEFAULT 'client';

-- Verify table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'trading_keys'
ORDER BY ordinal_position;
