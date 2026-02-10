-- Run this SQL query in Railway PostgreSQL to check Sharp's BitMart connectors
-- Copy and paste into Railway PostgreSQL query editor

-- Check connectors table
SELECT 
    c.id,
    c.name as connector_name,
    c.memo,
    c.api_key IS NOT NULL as has_api_key,
    c.api_secret IS NOT NULL as has_api_secret,
    c.client_id,
    cl.account_identifier,
    cl.name as client_name,
    c.created_at
FROM connectors c
LEFT JOIN clients cl ON cl.id = c.client_id
WHERE cl.account_identifier = 'client_new_sharp_foundation'
   OR cl.account_identifier LIKE '%sharp%'
   OR c.name ILIKE '%bitmart%'
   OR c.name ILIKE '%sharp%'
ORDER BY c.created_at DESC;

-- If no results, check clients table
SELECT 
    id, 
    account_identifier, 
    name, 
    wallet_address
FROM clients
WHERE account_identifier = 'client_new_sharp_foundation'
   OR account_identifier LIKE '%sharp%'
   OR name ILIKE '%sharp%';

-- Check exchange_credentials table (encrypted)
SELECT 
    ec.id,
    ec.exchange,
    ec.client_id,
    ec.api_key_encrypted IS NOT NULL as has_api_key,
    ec.api_secret_encrypted IS NOT NULL as has_api_secret,
    cl.account_identifier,
    cl.name as client_name
FROM exchange_credentials ec
LEFT JOIN clients cl ON cl.id = ec.client_id
WHERE cl.account_identifier = 'client_new_sharp_foundation'
   OR cl.account_identifier LIKE '%sharp%'
   OR ec.exchange ILIKE '%bitmart%';

-- Fix connector name if wrong (run only if needed)
-- UPDATE connectors 
-- SET name = 'bitmart' 
-- WHERE client_id = (SELECT id FROM clients WHERE account_identifier = 'client_new_sharp_foundation')
--   AND name ILIKE '%bitmart%'
--   AND name != 'bitmart';

-- Add memo/UID if missing (run only if you have the UID)
-- UPDATE connectors 
-- SET memo = 'YOUR_BITMART_UID_HERE' 
-- WHERE client_id = (SELECT id FROM clients WHERE account_identifier = 'client_new_sharp_foundation')
--   AND name = 'bitmart'
--   AND (memo IS NULL OR memo = '');
