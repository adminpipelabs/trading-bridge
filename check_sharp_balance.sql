-- Check Sharp's BitMart Balance
-- Run this in Railway → PostgreSQL → Query Tab

-- Step 1: Find Sharp's client and connectors
SELECT 
    c.id as client_id,
    c.name as client_name,
    c.account_identifier,
    conn.name as exchange,
    LEFT(conn.api_key, 15) || '...' as api_key_preview,
    CASE WHEN conn.api_secret IS NOT NULL THEN '***SET***' ELSE 'MISSING' END as api_secret_status,
    conn.memo as uid_memo,
    conn.created_at as connector_created
FROM clients c
LEFT JOIN connectors conn ON conn.client_id = c.id
WHERE c.name ILIKE '%sharp%' OR c.account_identifier ILIKE '%sharp%'
ORDER BY c.created_at DESC;

-- Step 2: Get full connector details (if needed for manual testing)
-- Uncomment and replace {client_id} with actual ID from Step 1
/*
SELECT 
    name,
    api_key,
    api_secret,
    memo
FROM connectors
WHERE client_id = '{client_id}' AND name = 'bitmart';
*/
