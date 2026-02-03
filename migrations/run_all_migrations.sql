-- ============================================================================
-- URGENT: Run Database Migrations
-- ============================================================================
-- This file contains both migrations needed for health monitoring and 
-- client self-service features.
--
-- Run this entire file against Railway PostgreSQL database.
-- 
-- Options:
--   1. Railway Dashboard → PostgreSQL service → Query tab (paste and execute)
--   2. psql: psql $DATABASE_URL -f migrations/run_all_migrations.sql
--   3. Any PostgreSQL client (pgAdmin, DBeaver, TablePlus)
--
-- ============================================================================

-- ============================================================================
-- MIGRATION 1: Health Monitor Columns
-- ============================================================================
-- Adds health tracking columns to bots table and creates bot_health_logs table

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
    bot_id VARCHAR(255) REFERENCES bots(id) ON DELETE CASCADE,
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

-- ============================================================================
-- MIGRATION 2: Trading Keys Table (for client self-service)
-- ============================================================================
-- Creates table for encrypted private key storage

CREATE TABLE IF NOT EXISTS trading_keys (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) UNIQUE NOT NULL,
    encrypted_key TEXT NOT NULL,
    chain VARCHAR(20) DEFAULT 'solana',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trading_keys_client_id ON trading_keys(client_id);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these after migrations to verify everything worked:

-- Check health columns exist
SELECT 
    column_name, 
    data_type, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'bots' 
  AND column_name IN ('health_status', 'health_message', 'last_trade_time', 'reported_status')
ORDER BY column_name;

-- Check bot_health_logs table exists
SELECT COUNT(*) as table_exists 
FROM information_schema.tables 
WHERE table_name = 'bot_health_logs';

-- Check trading_keys table exists
SELECT COUNT(*) as table_exists 
FROM information_schema.tables 
WHERE table_name = 'trading_keys';

-- View current bot statuses (should show health_status = 'unknown' initially)
SELECT id, name, status, health_status, health_message, reported_status 
FROM bots 
ORDER BY name;
