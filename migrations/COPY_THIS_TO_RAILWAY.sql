-- ============================================================
-- COPY THIS ENTIRE FILE TO RAILWAY DASHBOARD → POSTGRESQL → QUERY TAB
-- ============================================================
-- This migration creates:
-- 1. bot_health_logs table (for health monitoring)
-- 2. trading_keys table (for encrypted private key storage)
-- ============================================================

-- ============================================================
-- 1. Add health tracking columns to bots table
-- ============================================================
DO $$ 
BEGIN
    -- Add health_status column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bots' AND column_name = 'health_status') THEN
        ALTER TABLE bots ADD COLUMN health_status VARCHAR(20) DEFAULT 'unknown';
    END IF;
    
    -- Add health_message column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bots' AND column_name = 'health_message') THEN
        ALTER TABLE bots ADD COLUMN health_message TEXT;
    END IF;
    
    -- Add last_trade_time column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bots' AND column_name = 'last_trade_time') THEN
        ALTER TABLE bots ADD COLUMN last_trade_time TIMESTAMP;
    END IF;
    
    -- Add last_heartbeat column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bots' AND column_name = 'last_heartbeat') THEN
        ALTER TABLE bots ADD COLUMN last_heartbeat TIMESTAMP;
    END IF;
    
    -- Add reported_status column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bots' AND column_name = 'reported_status') THEN
        ALTER TABLE bots ADD COLUMN reported_status VARCHAR(20);
    END IF;
    
    -- Add status_updated_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bots' AND column_name = 'status_updated_at') THEN
        ALTER TABLE bots ADD COLUMN status_updated_at TIMESTAMP DEFAULT NOW();
    END IF;
END $$;

-- ============================================================
-- 2. Create bot_health_logs table
-- ============================================================
CREATE TABLE IF NOT EXISTS bot_health_logs (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) REFERENCES bots(id) ON DELETE CASCADE,
    checked_at TIMESTAMP DEFAULT NOW(),
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    health_status VARCHAR(20),
    reason TEXT,
    trade_count_since_last INTEGER DEFAULT 0,
    last_trade_found TIMESTAMP
);

-- Index for efficient queries
CREATE INDEX IF NOT EXISTS idx_bot_health_logs_bot_id ON bot_health_logs(bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_health_logs_checked_at ON bot_health_logs(checked_at);

-- ============================================================
-- 3. Create trading_keys table
-- ============================================================
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

-- Index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_trading_keys_client_id ON trading_keys(client_id);
CREATE INDEX IF NOT EXISTS idx_trading_keys_wallet_address ON trading_keys(wallet_address);

-- Add columns if table already exists (for existing deployments)
DO $$ 
BEGIN
    -- Add wallet_address column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'trading_keys' AND column_name = 'wallet_address') THEN
        ALTER TABLE trading_keys ADD COLUMN wallet_address VARCHAR(255);
    END IF;
    
    -- Add added_by column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'trading_keys' AND column_name = 'added_by') THEN
        ALTER TABLE trading_keys ADD COLUMN added_by VARCHAR(20) DEFAULT 'client';
    END IF;
END $$;

-- Add comments
COMMENT ON TABLE trading_keys IS 'Encrypted private keys for client self-service bot setup';
COMMENT ON COLUMN trading_keys.encrypted_key IS 'Fernet-encrypted private key (never decrypt in API responses)';
COMMENT ON COLUMN trading_keys.client_id IS 'Foreign key to clients.id (UNIQUE - one key per client)';
COMMENT ON COLUMN trading_keys.wallet_address IS 'Public wallet address derived from private key';
COMMENT ON COLUMN trading_keys.added_by IS 'Who added the key: "client" or "admin"';

-- ============================================================
-- VERIFICATION QUERIES (run these after migration to verify)
-- ============================================================
-- Check if tables exist:
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_name IN ('bot_health_logs', 'trading_keys');
-- Expected: bot_health_logs, trading_keys
--
-- Check if columns exist:
-- SELECT column_name FROM information_schema.columns 
-- WHERE table_name = 'bots' AND column_name IN ('health_status', 'reported_status', 'last_trade_time');
-- Expected: health_status, reported_status, last_trade_time
-- ============================================================
