-- Migration: Create trading_keys table for encrypted private key storage
-- Run against your Railway PostgreSQL database
-- Date: 2026-02-03

-- Create trading_keys table
CREATE TABLE IF NOT EXISTS trading_keys (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) UNIQUE NOT NULL,
    encrypted_key TEXT NOT NULL,
    chain VARCHAR(20) DEFAULT 'solana',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_trading_keys_client_id ON trading_keys(client_id);

-- Add comment
COMMENT ON TABLE trading_keys IS 'Encrypted private keys for client self-service bot setup';
COMMENT ON COLUMN trading_keys.encrypted_key IS 'Fernet-encrypted private key (never decrypt in API responses)';
COMMENT ON COLUMN trading_keys.client_id IS 'Foreign key to clients.id (UNIQUE - one key per client)';
