-- ============================================
-- COMPLETE DATABASE SETUP FOR CLIENT TESTING
-- Copy this entire file and run in Railway PostgreSQL Query tab
-- ============================================

-- ============================================
-- MIGRATION 1: Bot Health Monitor
-- ============================================

ALTER TABLE bots
ADD COLUMN IF NOT EXISTS last_heartbeat TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_trade_time TIMESTAMP,
ADD COLUMN IF NOT EXISTS health_status VARCHAR(20) DEFAULT 'unknown',
ADD COLUMN IF NOT EXISTS reported_status VARCHAR(20),
ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS health_message TEXT;

ALTER TABLE bots
ADD COLUMN IF NOT EXISTS chain VARCHAR(20),
ADD COLUMN IF NOT EXISTS bot_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}';

CREATE TABLE IF NOT EXISTS bot_health_logs (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255),
    checked_at TIMESTAMP DEFAULT NOW(),
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    health_status VARCHAR(20),
    reason TEXT,
    trade_count_since_last INTEGER DEFAULT 0,
    last_trade_found TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bot_health_logs_bot_id ON bot_health_logs(bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_health_logs_checked_at ON bot_health_logs(checked_at);
CREATE INDEX IF NOT EXISTS idx_bots_health_status ON bots(health_status);

UPDATE bots SET reported_status = status WHERE reported_status IS NULL;

-- ============================================
-- MIGRATION 2: Trading Keys (encrypted storage)
-- ============================================

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

CREATE INDEX IF NOT EXISTS idx_trading_keys_client_id ON trading_keys(client_id);

-- ============================================
-- MIGRATION 3: Fix Client Roles (security)
-- ============================================

UPDATE clients SET role = 'client' WHERE account_identifier != 'admin' OR account_identifier IS NULL;
UPDATE clients SET role = 'admin' WHERE account_identifier = 'admin';
UPDATE clients SET role = 'client' WHERE role IS NULL;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check client roles
SELECT id, name, account_identifier, role FROM clients ORDER BY role, name;

-- Check health columns exist
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'bots' 
AND column_name IN ('health_status', 'reported_status', 'last_trade_time', 'config');

-- Check trading_keys table exists
SELECT table_name FROM information_schema.tables WHERE table_name = 'trading_keys';

-- Check bot_health_logs table exists
SELECT table_name FROM information_schema.tables WHERE table_name = 'bot_health_logs';
