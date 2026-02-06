-- Migration: Add CEX Volume Bot Support
-- Run against your Railway PostgreSQL database
-- Date: 2026-02-06

-- Exchange credentials table
CREATE TABLE IF NOT EXISTS exchange_credentials (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_secret_encrypted TEXT NOT NULL,
    passphrase_encrypted TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, exchange)
);

CREATE INDEX IF NOT EXISTS idx_exchange_creds_client ON exchange_credentials(client_id);

-- Add exchange, base_asset, quote_asset columns to bots table
ALTER TABLE bots ADD COLUMN IF NOT EXISTS exchange VARCHAR(50);
ALTER TABLE bots ADD COLUMN IF NOT EXISTS base_asset VARCHAR(20);
ALTER TABLE bots ADD COLUMN IF NOT EXISTS quote_asset VARCHAR(20);

-- Trade logs table for CEX bots
CREATE TABLE IF NOT EXISTS trade_logs (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) NOT NULL,
    side VARCHAR(10) NOT NULL,
    amount DECIMAL(20, 8),
    price DECIMAL(20, 8),
    cost_usd DECIMAL(20, 2),
    order_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trade_logs_bot ON trade_logs(bot_id, created_at DESC);

-- Comments
COMMENT ON TABLE exchange_credentials IS 'Encrypted exchange API credentials for CEX volume bots';
COMMENT ON COLUMN exchange_credentials.api_key_encrypted IS 'Fernet-encrypted API key';
COMMENT ON COLUMN exchange_credentials.api_secret_encrypted IS 'Fernet-encrypted API secret';
COMMENT ON COLUMN exchange_credentials.passphrase_encrypted IS 'Fernet-encrypted passphrase (for exchanges like KuCoin)';
COMMENT ON TABLE trade_logs IS 'Trade execution logs for CEX volume bots';
