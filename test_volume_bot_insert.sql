-- Quick Test: Manual Volume Bot Insert
-- Run this to test if database/UI can handle volume bots
-- If volume bot appears in UI after this, problem is in backend creation logic

INSERT INTO bots (
    id, 
    client_id,
    account, 
    instance_name,
    name, 
    bot_type, 
    connector,
    exchange,
    pair,
    base_asset,
    quote_asset,
    strategy,
    status, 
    config, 
    stats,
    health_status,
    created_at,
    updated_at
)
VALUES (
    gen_random_uuid(),
    '7142fefa-3aaf-4883-a649-74738e4866dd',  -- Same client_id as spread bot
    'client_new_sharp_foundation',  -- Same account as spread bot
    'client_new_sharp_foundation_' || substr(gen_random_uuid()::text, 1, 8),
    'Sharp-VB-BitMart',  -- Volume Bot
    'volume',  -- ← Key: bot_type = volume
    'bitmart',
    'bitmart',
    'SHARP/USDT',
    'SHARP',
    'USDT',
    'volume',  -- strategy matches bot_type
    'created',
    '{"daily_volume_usd": 5000, "min_trade_usd": 10, "max_trade_usd": 25, "interval_min_seconds": 900, "interval_max_seconds": 2700, "slippage_bps": 50}'::jsonb,
    '{}'::jsonb,
    'unknown',
    NOW(),
    NOW()
)
RETURNING id, name, bot_type, account, client_id, status, created_at;

-- After running, check if volume bot appears in Sharp's dashboard
-- If YES → Database/UI are fine, problem is in backend creation logic
-- If NO → Problem is in UI query/filtering
