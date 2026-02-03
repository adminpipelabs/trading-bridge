-- ============================================================================
-- Verification Script: Check if migrations ran successfully
-- ============================================================================
-- Run this after running run_all_migrations.sql to verify everything worked

-- Check health columns exist in bots table
SELECT 
    'Health columns check' as check_type,
    CASE 
        WHEN COUNT(*) >= 6 THEN '✅ PASS - All health columns exist'
        ELSE '❌ FAIL - Missing health columns'
    END as result,
    COUNT(*) as columns_found
FROM information_schema.columns 
WHERE table_name = 'bots' 
  AND column_name IN (
    'health_status', 
    'health_message', 
    'last_trade_time', 
    'reported_status',
    'last_heartbeat',
    'status_updated_at'
  );

-- Check bot_health_logs table exists
SELECT 
    'bot_health_logs table' as check_type,
    CASE 
        WHEN COUNT(*) = 1 THEN '✅ PASS - Table exists'
        ELSE '❌ FAIL - Table missing'
    END as result,
    COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_name = 'bot_health_logs';

-- Check trading_keys table exists
SELECT 
    'trading_keys table' as check_type,
    CASE 
        WHEN COUNT(*) = 1 THEN '✅ PASS - Table exists'
        ELSE '❌ FAIL - Table missing'
    END as result,
    COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_name = 'trading_keys';

-- Show current bot health statuses
SELECT 
    'Bot health statuses' as check_type,
    COUNT(*) as total_bots,
    COUNT(CASE WHEN health_status IS NOT NULL THEN 1 END) as bots_with_health_status,
    COUNT(CASE WHEN health_status = 'unknown' THEN 1 END) as bots_unknown,
    COUNT(CASE WHEN health_status = 'healthy' THEN 1 END) as bots_healthy,
    COUNT(CASE WHEN health_status = 'stopped' THEN 1 END) as bots_stopped
FROM bots;

-- Detailed bot status view
SELECT 
    id,
    name,
    status as current_status,
    reported_status,
    health_status,
    health_message,
    last_trade_time,
    CASE 
        WHEN health_status IS NULL THEN '⚠️ Migration may not have run'
        WHEN health_status = 'unknown' THEN '⏳ Waiting for health check (runs every 5 min)'
        ELSE '✅ Health monitor active'
    END as migration_status
FROM bots
ORDER BY name;
