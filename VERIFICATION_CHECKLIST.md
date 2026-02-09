# Verification Checklist - Missing API Keys Fix

## ✅ What Was Fixed

1. **Bot runner now checks `connector` field first** (not just bot name)
2. **Multiple lookup strategies** (connector → bot name → fallback)
3. **Auto-clears health error** when credentials found
4. **Better logging** to debug credential lookup

---

## 🔍 How to Verify It's Fixed

### Step 1: Check Railway Deployment Status

**Railway Dashboard:**
- Go to your Railway project
- Check if latest deployment succeeded
- If it failed (network issue), wait a few minutes and retry

**Expected:** Deployment should succeed (code is correct)

---

### Step 2: Wait for Bot Runner Cycle

**Timing:**
- Bot runner checks every 1-2 minutes
- Health status updates automatically
- Error clears when credentials are found

**Wait:** 2-3 minutes after deployment succeeds

---

### Step 3: Check Bot Status

**In UI:**
1. Refresh the dashboard
2. Check bot cards:
   - ✅ **If credentials exist:** Error should disappear
   - ⚠️ **If credentials missing:** Error will still show (expected)

**What to look for:**
- ✅ **"Missing API keys" error gone** = Fix working!
- ⚠️ **Error still shows** = Credentials not saved (use Edit button to add)

---

### Step 4: Verify Credentials Are Found

**Check Railway Logs:**
Look for these log messages:

✅ **Success:**
```
✅ Bot {bot_id} - Using connector 'coinstore' as exchange
✅ Found API keys in exchange_credentials table for coinstore
✅ Cleared health error for bot {bot_id} - credentials found
```

❌ **Still Missing:**
```
⚠️ No credentials found in exchange_credentials table
   Available exchanges for this client: [...]
```

---

## 🎯 Expected Results

### Scenario 1: Credentials Were Saved During Creation ✅

**Result:**
- Error disappears automatically within 1-2 minutes
- Bot status changes from "error" to "healthy" or "stopped"
- No action needed from client

### Scenario 2: Credentials Were NOT Saved ❌

**Result:**
- Error still shows (expected - credentials don't exist)
- Client can click **Edit** button
- Add API keys via Edit modal
- Error clears immediately after saving

---

## 🚨 If Error Persists

### Check 1: Verify Credentials Exist in Database

```sql
SELECT 
    exchange,
    client_id,
    api_key_encrypted IS NOT NULL as has_key
FROM exchange_credentials
WHERE client_id = 'YOUR_CLIENT_ID';
```

**If no rows:** Credentials weren't saved → Use Edit button to add

### Check 2: Verify Bot's Connector Field

```sql
SELECT 
    id,
    name,
    connector,
    client_id,
    health_message
FROM bots
WHERE id = 'YOUR_BOT_ID';
```

**Check:** Does `connector` match the exchange name in `exchange_credentials`?

### Check 3: Check Railway Logs

Look for:
- `✅ Found API keys` = Credentials found
- `⚠️ No credentials found` = Credentials missing
- `🔍 Bot {bot_id} - Trying connector_name` = Multiple lookups tried

---

## ✅ Quick Test

1. **Wait 2-3 minutes** after Railway deployment succeeds
2. **Refresh dashboard**
3. **Check bot cards:**
   - If error gone → ✅ Fix working!
   - If error still shows → Check logs or use Edit button

---

## Summary

✅ **Fix is deployed** (once Railway retries successfully)  
✅ **Auto-fixes existing bots** (if credentials exist)  
✅ **No client action needed** (if credentials were saved)  
✅ **Edit button available** (if credentials missing)

**You can check now** - wait for Railway to deploy, then refresh dashboard!
