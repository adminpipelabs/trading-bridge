-- Migration: Add bot health tracking columns
-- Run against your Railway PostgreSQL database
-- Date: 2026-02-03

-- Add health monitoring columns to bots table
ALTER TABLE bots
ADD COLUMN IF NOT EXISTS last_heartbeat TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_trade_time TIMESTAMP,
ADD COLUMN IF NOT EXISTS health_status VARCHAR(20) DEFAULT 'unknown',
ADD COLUMN IF NOT EXISTS reported_status VARCHAR(20),
ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS health_message TEXT;

-- Ensure chain and config columns exist (needed for Solana routing)
-- These may already exist if you added them during Lynk setup
ALTER TABLE bots
ADD COLUMN IF NOT EXISTS chain VARCHAR(20),
ADD COLUMN IF NOT EXISTS bot_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}';

-- Ensure wallets table has the address we need for Solana health checks
-- (should already exist from your schema)
-- ALTER TABLE wallets ADD COLUMN IF NOT EXISTS address VARCHAR(255);

-- health_status values: 'healthy', 'stale', 'stopped', 'unknown', 'error'
-- reported_status: what the user/API last set it to ('running', 'stopped')
-- status: remains the source-of-truth display status (existing column)

-- Create health check log table for audit trail
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

-- Index for efficient health queries
CREATE INDEX IF NOT EXISTS idx_bot_health_logs_bot_id ON bot_health_logs(bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_health_logs_checked_at ON bot_health_logs(checked_at);
CREATE INDEX IF NOT EXISTS idx_bots_health_status ON bots(health_status);

-- Migrate existing data: set reported_status from current status
UPDATE bots SET reported_status = status WHERE reported_status IS NULL;

COMMENT ON COLUMN bots.health_status IS 'Actual health determined by monitoring: healthy, stale, stopped, unknown, error';
COMMENT ON COLUMN bots.reported_status IS 'Last status set by user action (start/stop)';
COMMENT ON COLUMN bots.last_heartbeat IS 'Last time a heartbeat was received from this bot';
COMMENT ON COLUMN bots.last_trade_time IS 'Last time a trade was detected for this bot';
