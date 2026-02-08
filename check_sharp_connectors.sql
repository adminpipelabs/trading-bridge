-- Check connectors table for Sharp's BitMart API keys
-- Run this in Railway PostgreSQL to verify connector name and memo

SELECT 
    c.id,
    c.client_id,
    c.name as connector_name,
    c.api_key,
    c.api_secret,
    c.memo,
    cl.account_identifier,
    cl.name as client_name
FROM connectors c
JOIN clients cl ON cl.id = c.client_id
WHERE cl.account_identifier = 'client_new_sharp_foundation'
   OR cl.account_identifier LIKE '%sharp%'
   OR c.name ILIKE '%bitmart%'
ORDER BY c.created_at DESC;

-- Also check exchange_credentials table (encrypted)
SELECT 
    ec.id,
    ec.client_id,
    ec.exchange,
    ec.api_key_encrypted IS NOT NULL as has_api_key,
    ec.api_secret_encrypted IS NOT NULL as has_api_secret,
    ec.passphrase_encrypted IS NOT NULL as has_passphrase,
    cl.account_identifier,
    cl.name as client_name
FROM exchange_credentials ec
JOIN clients cl ON cl.id = ec.client_id
WHERE cl.account_identifier = 'client_new_sharp_foundation'
   OR cl.account_identifier LIKE '%sharp%'
   OR ec.exchange ILIKE '%bitmart%'
ORDER BY ec.created_at DESC;
