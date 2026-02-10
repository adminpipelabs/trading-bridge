-- Quick check if Volume Bot has executed trades
-- Run this in Railway PostgreSQL Query tab

-- Step 1: Find the Volume Bot
SELECT 
    id,
    name,
    status,
    exchange,
    health_status,
    health_message,
    last_trade_time,
    updated_at
FROM bots
WHERE name LIKE '%Volume Bot%Coinstore%'
ORDER BY updated_at DESC
LIMIT 1;

-- Step 2: Check if trade_logs table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'trade_logs'
) as table_exists;

-- Step 3: Check trades for the bot (replace {bot_id} with ID from Step 1)
-- First, get the bot_id from Step 1, then run:
/*
SELECT 
    COUNT(*) as total_trades,
    SUM(cost_usd) as total_volume_usd,
    SUM(CASE WHEN side = 'buy' THEN cost_usd ELSE 0 END) as buy_volume,
    SUM(CASE WHEN side = 'sell' THEN cost_usd ELSE 0 END) as sell_volume,
    COUNT(CASE WHEN side = 'buy' THEN 1 END) as buy_count,
    COUNT(CASE WHEN side = 'sell' THEN 1 END) as sell_count,
    AVG(cost_usd) as avg_trade_size,
    MIN(created_at) as first_trade,
    MAX(created_at) as last_trade,
    EXTRACT(EPOCH FROM (NOW() - MAX(created_at)))/60 as minutes_since_last_trade
FROM trade_logs
WHERE bot_id = '{bot_id}';
*/

-- Step 4: Get recent trades (replace {bot_id})
/*
SELECT 
    id,
    side,
    amount,
    price,
    cost_usd,
    order_id,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_ago
FROM trade_logs
WHERE bot_id = '{bot_id}'
ORDER BY created_at DESC
LIMIT 10;
*/

-- Step 5: Combined query (all in one)
SELECT 
    b.id as bot_id,
    b.name as bot_name,
    b.status as bot_status,
    b.health_status,
    b.last_trade_time,
    COUNT(tl.id) as trade_count,
    COALESCE(SUM(tl.cost_usd), 0) as total_volume_usd,
    COALESCE(SUM(CASE WHEN tl.side = 'buy' THEN tl.cost_usd ELSE 0 END), 0) as buy_volume,
    COALESCE(SUM(CASE WHEN tl.side = 'sell' THEN tl.cost_usd ELSE 0 END), 0) as sell_volume,
    COUNT(CASE WHEN tl.side = 'buy' THEN 1 END) as buy_count,
    COUNT(CASE WHEN tl.side = 'sell' THEN 1 END) as sell_count,
    COALESCE(AVG(tl.cost_usd), 0) as avg_trade_size,
    MAX(tl.created_at) as last_trade_time_from_logs,
    CASE 
        WHEN MAX(tl.created_at) IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (NOW() - MAX(tl.created_at)))/60
        ELSE NULL
    END as minutes_since_last_trade
FROM bots b
LEFT JOIN trade_logs tl ON tl.bot_id = b.id
WHERE b.name LIKE '%Volume Bot%Coinstore%'
GROUP BY b.id, b.name, b.status, b.health_status, b.last_trade_time
ORDER BY b.updated_at DESC
LIMIT 1;
