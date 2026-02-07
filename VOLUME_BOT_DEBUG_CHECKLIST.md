# Volume Bot Debug Checklist - For CTO/Dev

## Quick Test: Manual SQL Insert

**Run this SQL to test if database/UI can handle volume bots:**

```sql
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
);
```

**After running:**
1. Refresh Sharp's dashboard
2. Check if volume bot appears

**If volume bot appears** → Database/UI are fine, problem is in backend creation logic ✅  
**If volume bot doesn't appear** → Problem is in UI query/filtering ❌

---

## Step 1: Check Railway Backend Logs

When Sharp creates a volume bot, check Railway logs for:

### ✅ Success Path (What we expect):
```
🟢 CLIENT SETUP: Creating bot via /clients/{id}/setup-bot
   Client: New Sharp Foundation (id=7142fefa-3aaf-4883-a649-74738e4866dd, account=client_new_sharp_foundation)
   Bot: name=..., bot_type=volume, exchange=bitmart, is_cex=True
   Bot object created: account=client_new_sharp_foundation, bot_type=volume
   After save: bot.account=client_new_sharp_foundation, bot.bot_type=volume, bot.client_id=7142fefa-3aaf-4883-a649-74738e4866dd
✅ Bot setup completed successfully for client 7142fefa-3aaf-4883-a649-74738e4866dd, bot_id: {bot_id}
   Final bot state: account=client_new_sharp_foundation, bot_type=volume, name=...
```

### ❌ Error Path (What to look for):
```
❌ Unexpected error in setup_bot for client {id}: {error}
⚠️ WARNING: Bot bot_type mismatch! Expected: volume, Got: {something_else}
Failed to set up bot: {error_message}
```

**Questions to answer:**
1. Does the request hit the backend? (Look for "Setup bot request for client_id")
2. Any errors/exceptions thrown? (Look for "ERROR" or "Exception")
3. Does it reach the database INSERT? (Look for "After save: bot.account")
4. Any rollback? (Look for "rollback" or "Transaction")

---

## Step 2: Compare Request Payloads

Open browser **Network tab** (F12 → Network), create each bot type, and compare:

### Spread Bot Request
**URL**: `POST /clients/7142fefa-3aaf-4883-a649-74738e4866dd/setup-bot`

**Payload**:
```json
{
  "name": "SHARP Spread Bot",
  "bot_type": "spread",
  "exchange": "bitmart",
  "connector": "bitmart",
  "chain": "evm",
  "pair": "SHARP/USDT",
  "base_asset": "SHARP",
  "quote_asset": "USDT",
  "base_mint": null,
  "private_key": null,
  "config": {
    "spread_bps": 50,
    "order_size_usd": 100,
    "levels": 3,
    "refresh_seconds": 30,
    "max_position_usd": 1000
  }
}
```

### Volume Bot Request
**URL**: `POST /clients/7142fefa-3aaf-4883-a649-74738e4866dd/setup-bot`

**Payload** (to be filled):
```json
{
  "name": "SHARP Volume Bot",
  "bot_type": "volume",
  "exchange": "bitmart",
  "connector": "bitmart",
  "chain": "evm",
  "pair": "SHARP/USDT",
  "base_asset": "SHARP",
  "quote_asset": "USDT",
  "base_mint": null,
  "private_key": null,
  "config": {
    "daily_volume_usd": 5000,
    "min_trade_usd": 10,
    "max_trade_usd": 25,
    "interval_min_seconds": 900,
    "interval_max_seconds": 2700,
    "slippage_bps": 50
  }
}
```

### Comparison Table

| Field | Spread Bot Request | Volume Bot Request | Match? |
|-------|-------------------|-------------------|--------|
| `bot_type` | `"spread"` | `"volume"` | ✅ Different (expected) |
| `exchange` | `"bitmart"` | `"bitmart"` | ✅ Same |
| `connector` | `"bitmart"` | `"bitmart"` | ✅ Same |
| `chain` | `"evm"` | `"evm"` | ✅ Same |
| `pair` | `"SHARP/USDT"` | `"SHARP/USDT"` | ✅ Same |
| `base_asset` | `"SHARP"` | `"SHARP"` | ✅ Same |
| `quote_asset` | `"USDT"` | `"USDT"` | ✅ Same |
| `private_key` | `null` | `null` | ✅ Same |
| `config.daily_volume_usd` | ❌ Not present | ✅ Present | ⚠️ Different |
| `config.spread_bps` | ✅ Present | ❌ Not present | ⚠️ Different |
| `config.order_size_usd` | ✅ Present | ❌ Not present | ⚠️ Different |

**Expected differences**: Config fields differ (spread_bps vs daily_volume_usd) - this is normal ✅

**Unexpected differences**: Check if any required fields are missing in volume bot request ❌

---

## Step 3: Check Response

### Spread Bot Response (Success)
```json
{
  "success": true,
  "bot_id": "74d9b480-f15b-444d-a290-a798b59c584a",
  "message": "Bot created successfully. Your private key has been encrypted and stored securely."
}
```

### Volume Bot Response (To be checked)
```json
{
  "success": ?,
  "bot_id": ?,
  "message": ?
}
```

**Questions:**
- Does volume bot get `success: true`?
- Does it get a `bot_id`?
- What's the `message`?

---

## Step 4: Database Verification

After volume bot creation attempt, run:

```sql
-- Check all bots for this client
SELECT 
    id, 
    name, 
    bot_type, 
    account, 
    client_id, 
    status, 
    created_at,
    error
FROM bots 
WHERE client_id = '7142fefa-3aaf-4883-a649-74738e4866dd'
ORDER BY created_at DESC;
```

**Expected**: Should see both spread and volume bots  
**Actual**: Only spread bot exists ❌

---

## Step 5: Check Exchange Credentials

Verify credentials exist for volume bot:

```sql
SELECT 
    client_id, 
    exchange, 
    created_at 
FROM exchange_credentials 
WHERE client_id = '7142fefa-3aaf-4883-a649-74738e4866dd' 
AND exchange = 'bitmart';
```

**Expected**: Should return 1 row (credentials exist)  
**If missing**: Volume bot creation will fail with "API keys not connected" error

---

## Execution Path Differences

Since both bots use the same endpoint, check for differences in execution:

### CEX Bot Flow (Both Volume and Spread)
1. ✅ Validate bot_type (both pass)
2. ✅ Check exchange credentials exist (both should pass)
3. ✅ Create Bot object (both should work)
4. ✅ Save to database (spread works, volume fails?)
5. ✅ Update exchange/chain/base_asset/quote_asset (both should work)
6. ✅ Start bot in background (both should work)

### Potential Failure Points

**Point 1: Exchange Credentials Check** (line 375-388)
```python
creds_check = db.execute(text("""
    SELECT id FROM exchange_credentials 
    WHERE client_id = :client_id AND exchange = :exchange
"""), {
    "client_id": client_id,
    "exchange": exchange_lower
}).first()

if not creds_check:
    raise HTTPException(status_code=400, detail="API keys not connected")
```
**Check**: Does this pass for volume bot?

**Point 2: Bot Object Creation** (line 565-578)
```python
bot = Bot(
    id=bot_id,
    client_id=client_id,
    account=client.account_identifier,
    bot_type=request.bot_type,  # Should be "volume"
    ...
)
```
**Check**: Is bot_type set correctly?

**Point 3: Database Save** (line 583-584)
```python
db.add(bot)
db.flush()
```
**Check**: Does flush succeed?

**Point 4: Bot Type Verification** (line 590-598)
```python
if bot.bot_type != request.bot_type:
    logger.error(f"⚠️ WARNING: Bot bot_type mismatch!")
    # Fix via SQL
```
**Check**: Does this trigger for volume bot?

**Point 5: Transaction Commit** (line 597, 607, 628, 657)
Multiple `db.commit()` calls - check if any fail

---

## Summary

**Quick Test**: Run SQL insert → If volume bot appears, problem is in backend creation logic ✅

**Detailed Check**: 
1. Railway logs → See actual error
2. Network tab → Compare request payloads
3. Database query → Verify bot doesn't exist
4. Credentials check → Verify they exist

**Most Likely Issue**: Transaction rollback or silent failure in database save step.
