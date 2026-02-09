# Existing Bots API Keys - Do They Need to Re-enter?

## Answer: **It Depends** - Check First, Then Fix

## How Bot Runner Finds API Keys

The bot runner checks **TWO places** for API keys (in order):

1. **`connectors` table** (plaintext) - Checked FIRST
2. **`exchange_credentials` table** (encrypted) - Checked SECOND as fallback

## For Existing Bots Created Before Fix

### Scenario 1: API Keys Were Added Separately ✅
**If clients added API keys via:**
- `/exchanges/credentials` endpoint
- Admin added them via `/clients/{client_id}/connectors`
- They were saved to `connectors` table

**Result**: ✅ **Keys are already saved** - Bot should work, no re-entry needed

### Scenario 2: API Keys Were ONLY Entered During Bot Creation ❌
**If clients ONLY entered keys in bot creation wizard:**
- Frontend didn't send them to backend
- They were never saved anywhere

**Result**: ❌ **Keys are lost** - Need to re-enter via endpoint

## How to Check

### Step 1: Check if Keys Exist in `connectors` Table

```sql
-- Get client_id from bot
SELECT client_id FROM bots WHERE id = 'your-bot-id';

-- Check connectors table
SELECT name, 
       api_key IS NOT NULL as has_api_key,
       api_secret IS NOT NULL as has_api_secret,
       memo IS NOT NULL as has_memo
FROM connectors 
WHERE client_id = 'your-client-id'
  AND LOWER(name) IN ('bitmart', 'coinstore');
```

**If you see rows with `has_api_key = true`**: ✅ Keys exist, bot should work

### Step 2: Check if Keys Exist in `exchange_credentials` Table

```sql
-- Check exchange_credentials table
SELECT exchange,
       api_key_encrypted IS NOT NULL as has_api_key,
       api_secret_encrypted IS NOT NULL as has_api_secret,
       passphrase_encrypted IS NOT NULL as has_passphrase
FROM exchange_credentials 
WHERE client_id = 'your-client-id'
  AND LOWER(exchange) IN ('bitmart', 'coinstore');
```

**If you see rows with `has_api_key = true`**: ✅ Keys exist, bot should work

### Step 3: Check Bot Status

```sql
-- Check bot error status
SELECT id, name, health_status, health_message, error
FROM bots 
WHERE id = 'your-bot-id';
```

**If `health_message = 'Missing API keys'`**: ❌ Keys are missing, need to add

## What to Do

### If Keys Exist (Scenario 1) ✅
- **No action needed** - Bot should work
- If bot still shows "Missing API keys", check:
  - Connector name matches exchange name (case-insensitive)
  - Bot's `connector` field matches connector's `name` field

### If Keys Don't Exist (Scenario 2) ❌
- **Need to add keys** - Use one of these methods:

#### Option A: Use New Endpoint (Easiest)
```bash
POST /bots/{bot_id}/add-exchange-credentials?api_key=...&api_secret=...&passphrase=...
```

#### Option B: Use Credentials Endpoint
```bash
POST /exchanges/credentials
{
  "client_id": "...",
  "exchange": "bitmart",
  "api_key": "...",
  "api_secret": "...",
  "passphrase": "..."
}
```

## Quick Check Script

Run this SQL to check all volume bots:

```sql
-- Check all volume bots and their API key status
SELECT 
    b.id,
    b.name,
    b.connector,
    b.health_status,
    b.health_message,
    -- Check connectors table
    CASE WHEN c.api_key IS NOT NULL THEN '✅ In connectors' ELSE '❌ Missing' END as connectors_status,
    -- Check exchange_credentials table
    CASE WHEN ec.api_key_encrypted IS NOT NULL THEN '✅ In exchange_credentials' ELSE '❌ Missing' END as exchange_creds_status
FROM bots b
LEFT JOIN clients cl ON cl.account_identifier = b.account
LEFT JOIN connectors c ON c.client_id = cl.id 
    AND LOWER(c.name) = LOWER(COALESCE(b.exchange, b.connector))
LEFT JOIN exchange_credentials ec ON ec.client_id = cl.id 
    AND LOWER(ec.exchange) = LOWER(COALESCE(b.exchange, b.connector))
WHERE b.bot_type = 'volume'
ORDER BY b.created_at DESC;
```

## Summary

**Do existing bots need to re-enter keys?**

- **Maybe** - Depends on whether keys were saved separately
- **Check first** - Use SQL queries above
- **If missing** - Use `/bots/{bot_id}/add-exchange-credentials` endpoint
- **If present** - Bot should work, check connector name matching

**Most likely scenario**: If clients entered keys ONLY during bot creation (before frontend fix), keys were **never saved** and need to be re-entered.
