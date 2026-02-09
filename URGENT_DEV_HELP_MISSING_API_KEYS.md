# 🚨 URGENT DEV HELP NEEDED - Missing API Keys Error Persists

## Problem

**Error still showing:** "Missing API keys - add connector or exchange credentials"  
**Even though:** API keys were added during bot creation  
**Status:** Clients are frustrated - we said it was fixed but it's not

---

## What We've Tried

### Fix 1: Updated Bot Runner Lookup Logic ✅
- Changed to check `connector` field first (not just bot name)
- Added multiple fallback strategies
- Added auto-clear health error when credentials found

**Commit:** `52fd765` - "Fix bot runner to find credentials using connector field"

### Fix 2: Added Edit Modal for API Keys ✅
- Clients can add keys via Edit button
- Saves to `exchange_credentials` table

**But:** Clients shouldn't need to re-enter keys they already added!

---

## What We Need Dev To Check

### 1. **Verify Credentials Are Actually Saved**

**Check if credentials exist in database:**

```sql
-- Get bot details
SELECT 
    b.id,
    b.name,
    b.connector,
    b.client_id,
    b.account,
    b.health_status,
    b.health_message
FROM bots b
WHERE b.name LIKE '%Coinstore%' OR b.name LIKE '%BitMart%';

-- Check if credentials exist for these bots' clients
SELECT 
    ec.exchange,
    ec.client_id,
    ec.api_key_encrypted IS NOT NULL as has_key,
    ec.api_secret_encrypted IS NOT NULL as has_secret,
    ec.updated_at
FROM exchange_credentials ec
WHERE ec.client_id IN (
    SELECT DISTINCT client_id FROM bots 
    WHERE name LIKE '%Coinstore%' OR name LIKE '%BitMart%'
);
```

**Questions:**
- Do credentials exist in `exchange_credentials` table?
- Does `exchange` field match bot's `connector` field?
- Is `client_id` correct?

---

### 2. **Check Bot Runner Query**

**File:** `app/cex_bot_runner.py` lines 90-103

**Current query:**
```python
all_bots = await conn.fetch("""
    SELECT b.*, 
           c.api_key,
           c.api_secret,
           c.memo,
           c.name as connector_name,
           cl.id as client_id,
           cl.account_identifier
    FROM bots b
    JOIN clients cl ON cl.account_identifier = b.account
    LEFT JOIN connectors c ON c.client_id = cl.id
    WHERE b.status = 'running'
      AND b.bot_type = 'volume'
""")
```

**Questions:**
- Is `client_id` being retrieved correctly?
- Is the JOIN working properly?
- Are credentials in `connectors` table or `exchange_credentials` table?

---

### 3. **Check Credential Lookup Logic**

**File:** `app/cex_bot_runner.py` lines 167-217

**Current logic:**
1. Extract exchange from `connector` field first
2. Fallback to bot name extraction
3. Query `exchange_credentials` table with `client_id` and `exchange`

**Questions:**
- Is `expected_exchange` matching what's saved in database?
- Is `client_id` correct when querying?
- Is the SQL query case-sensitive? (Should use LOWER() consistently)

---

### 4. **Check Bot Creation Flow**

**File:** `app/client_setup_routes.py` lines 383-435

**When bot is created:**
- API keys are saved to `exchange_credentials` table
- Exchange name saved as: `request.exchange.lower()`
- Bot's `connector` field set to: `request.connector or request.exchange`

**Questions:**
- Are API keys actually being saved? (Check logs for "✅ Saved API credentials")
- Is the transaction committing successfully?
- Is there a rollback happening?

---

## Debugging Steps Needed

### Step 1: Check Railway Logs

**Look for:**
```
💾 Saving API credentials for coinstore bot creation
✅ Saved API credentials for coinstore
```

**If missing:** Credentials weren't saved during creation

### Step 2: Check Bot Runner Logs

**Look for:**
```
🔍 Bot {bot_id} - connector 'coinstore' doesn't match expected 'coinstore' or missing keys
⚠️ No credentials found in exchange_credentials table
   Bot ID: {bot_id}
   Client ID: {client_id}
   Expected exchange: coinstore
   Available exchanges for this client: [...]
```

**This will show:**
- What exchange name bot runner is looking for
- What client_id it's using
- What exchanges exist for that client

### Step 3: Verify Database State

**Run these queries:**

```sql
-- 1. Check bot details
SELECT id, name, connector, client_id, account, health_message
FROM bots
WHERE name LIKE '%Coinstore%' OR name LIKE '%BitMart%';

-- 2. Check credentials for those clients
SELECT exchange, client_id, 
       api_key_encrypted IS NOT NULL as has_key,
       updated_at
FROM exchange_credentials
WHERE client_id IN (
    SELECT DISTINCT client_id FROM bots 
    WHERE name LIKE '%Coinstore%' OR name LIKE '%BitMart%'
);

-- 3. Check connectors table (alternative location)
SELECT name, client_id,
       api_key IS NOT NULL as has_key,
       api_secret IS NOT NULL as has_secret
FROM connectors
WHERE client_id IN (
    SELECT DISTINCT client_id FROM bots 
    WHERE name LIKE '%Coinstore%' OR name LIKE '%BitMart%'
)
AND LOWER(name) IN ('coinstore', 'bitmart');
```

---

## Possible Root Causes

### 1. **Exchange Name Mismatch** ⚠️ MOST LIKELY
- Credentials saved as: `exchange = "coinstore"`
- Bot runner looking for: `exchange = "Coinstore"` (capitalized)
- **Fix:** Ensure consistent lowercase everywhere

### 2. **Client ID Mismatch**
- Bot's `client_id` doesn't match credentials' `client_id`
- **Fix:** Verify JOIN logic in bot runner query

### 3. **Credentials Not Actually Saved**
- Transaction rolled back during bot creation
- Error during encryption
- **Fix:** Check bot creation logs for errors

### 4. **Bot Runner Not Running**
- Health check hasn't run yet
- Bot runner service not started
- **Fix:** Check Railway logs for bot runner startup

---

## Immediate Actions Needed

1. **Check Railway logs** for bot creation (did credentials save?)
2. **Check Railway logs** for bot runner (is it finding credentials?)
3. **Run SQL queries** to verify database state
4. **Check bot's `connector` field** matches `exchange` in credentials
5. **Verify `client_id`** matches between bot and credentials

---

## What We Need

**Please help us:**
1. ✅ Verify credentials exist in database
2. ✅ Check if bot runner is querying correctly
3. ✅ Identify why lookup is failing
4. ✅ Fix the root cause (not just workaround)

**We've tried fixes but error persists - need dev expertise to debug properly.**

---

## Current Status

- ✅ Code fixes pushed to GitHub
- ✅ Edit button allows adding keys (workaround)
- ❌ **Root cause not fixed** - credentials not being found
- ❌ **Clients frustrated** - told them it was fixed but it's not

**We need dev help to properly debug and fix this issue.**
