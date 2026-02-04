-- ============================================
-- CLIENT DASHBOARD FIXES - Database Migrations
-- Run this after COMPLETE_SETUP.sql
-- ============================================

-- Add management_mode column to clients table
ALTER TABLE clients
ADD COLUMN IF NOT EXISTS management_mode VARCHAR(20) DEFAULT 'unset';
-- Values: 'self' (client manages), 'managed' (Pipe Labs manages), 'unset' (hasn't chosen yet)

-- Create admin_notifications table
CREATE TABLE IF NOT EXISTS admin_notifications (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,          -- key_connected, bot_started, bot_stopped, client_signup, payment_received, management_mode
    client_id VARCHAR(255),
    message TEXT,
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_notifications_read ON admin_notifications(read);
CREATE INDEX IF NOT EXISTS idx_admin_notifications_created ON admin_notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_notifications_client ON admin_notifications(client_id);

-- Set default management_mode for existing clients
UPDATE clients SET management_mode = 'self' WHERE management_mode IS NULL OR management_mode = '';

-- Verification queries
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'clients' AND column_name = 'management_mode';

SELECT table_name FROM information_schema.tables WHERE table_name = 'admin_notifications';

SELECT COUNT(*) as total_notifications FROM admin_notifications;
