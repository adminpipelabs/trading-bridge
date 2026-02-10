-- Reset Volume Bot for immediate execution
-- Run this in Railway PostgreSQL Query tab

UPDATE bots 
SET last_trade_time = NULL,
    health_message = 'Reset for immediate execution - market order will execute on next cycle'
WHERE name LIKE '%Volume Bot%Coinstore%'
  AND status = 'running';

-- Verify the reset
SELECT id, name, status, last_trade_time, health_message
FROM bots
WHERE name LIKE '%Volume Bot%Coinstore%'
ORDER BY updated_at DESC
LIMIT 1;
