-- URGENT FIX: Backfill pair/base_mint from config JSON for existing bots
-- This fixes "Bot missing pair configuration" error for Lynk and other clients

-- Check current state
SELECT id, name, pair, base_asset, quote_asset, base_mint, 
       config->>'pair' as config_pair,
       config->>'base_mint' as config_base_mint,
       config->>'base_asset' as config_base_asset,
       config->>'quote_asset' as config_quote_asset
FROM bots 
WHERE name LIKE '%Lynk%' OR account LIKE '%lynk%'
ORDER BY created_at DESC;

-- Fix 1: Backfill pair from config JSON if column is NULL
UPDATE bots 
SET pair = config->>'pair'
WHERE pair IS NULL 
  AND config->>'pair' IS NOT NULL 
  AND config->>'pair' != '';

-- Fix 2: Backfill base_mint from config JSON if column is NULL
UPDATE bots 
SET base_mint = config->>'base_mint'
WHERE base_mint IS NULL 
  AND config->>'base_mint' IS NOT NULL 
  AND config->>'base_mint' != '';

-- Fix 3: Build pair from base_asset/quote_asset if pair is NULL
UPDATE bots 
SET pair = CONCAT(base_asset, '/', quote_asset)
WHERE pair IS NULL 
  AND base_asset IS NOT NULL 
  AND quote_asset IS NOT NULL
  AND base_asset != ''
  AND quote_asset != '';

-- Fix 4: Build pair from config base_asset/quote_asset if pair is NULL
UPDATE bots 
SET pair = CONCAT(config->>'base_asset', '/', config->>'quote_asset')
WHERE pair IS NULL 
  AND config->>'base_asset' IS NOT NULL 
  AND config->>'quote_asset' IS NOT NULL
  AND config->>'base_asset' != ''
  AND config->>'quote_asset' != '';

-- Fix 5: Set base_asset/quote_asset from config if columns are NULL
UPDATE bots 
SET base_asset = config->>'base_asset'
WHERE base_asset IS NULL 
  AND config->>'base_asset' IS NOT NULL 
  AND config->>'base_asset' != '';

UPDATE bots 
SET quote_asset = config->>'quote_asset'
WHERE quote_asset IS NULL 
  AND config->>'quote_asset' IS NOT NULL 
  AND config->>'quote_asset' != '';

-- Verify fixes
SELECT id, name, pair, base_asset, quote_asset, base_mint,
       CASE 
         WHEN pair IS NOT NULL THEN '✅ Has pair'
         WHEN base_mint IS NOT NULL THEN '✅ Has base_mint'
         WHEN base_asset IS NOT NULL AND quote_asset IS NOT NULL THEN '✅ Has base/quote'
         ELSE '❌ Still missing'
       END as status
FROM bots 
WHERE name LIKE '%Lynk%' OR account LIKE '%lynk%'
ORDER BY created_at DESC;
