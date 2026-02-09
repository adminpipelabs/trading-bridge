# Fix "Missing API Keys" Error - Complete Guide

## What This Error Means

The bot runner checks **TWO places** for API keys:
1. **`connectors` table** (checked first)
2. **`exchange_credentials` table** (checked second)

If keys aren't found in **either** place, you get: **"Missing API keys - add connector or exchange credentials"**

---

## Why This Happens Even If Keys Were Added During Creation

### Possible Causes:

1. **Exchange Name Mismatch** ⚠️ **MOST COMMON**
   - Bot has `connector = "Coinstore"` (capitalized)
   - But credentials saved as `exchange = "coinstore"` (lowercase)
   - Bot runner does case-insensitive lookup, but there might be a mismatch

2. **Keys Not Actually Saved**
   - Frontend sent keys, but backend failed to save them (error during encryption)
   - Transaction rolled back due to error

3. **Bot Created Before Fix**
   - Bot created before frontend was updated to send API keys
   - Keys were never sent, so never saved

---

## Do You Need to Delete and Recreate? **NO!** ✅

**You can fix existing bots WITHOUT deleting them:**

### Option 1: Use Edit Button (Easiest) ✅ **RECOMMENDED**

1. Click **Edit** button on the bot card
2. Expand **"Add API Keys"** section
3. Enter your API Key, Secret, and Passphrase (if needed)
4. Click **Save**
5. The error message will disappear on next health check (within 1-2 minutes)

### Option 2: Use API Endpoint Directly

```bash
POST /bots/{bot_id}/add-exchange-credentials?api_key=YOUR_KEY&api_secret=YOUR_SECRET&passphrase=YOUR_PASSPHRASE
```

---

## Will the Message Disappear 100%? ✅ **YES**

**Once credentials are saved correctly:**
- Bot runner checks every cycle (every few minutes)
- When it finds credentials, it clears the error:
  ```python
  UPDATE bots SET health_status = 'healthy', health_message = NULL
  ```
- Error disappears within **1-2 minutes** after saving credentials

---

## How to Verify Keys Are Saved

### Check Database:

```sql
-- Check exchange_credentials table
SELECT 
    exchange,
    client_id,
    api_key_encrypted IS NOT NULL as has_key,
    api_secret_encrypted IS NOT NULL as has_secret,
    updated_at
FROM exchange_credentials
WHERE client_id = 'YOUR_CLIENT_ID'
  AND LOWER(exchange) IN ('coinstore', 'bitmart');
```

**If you see rows with `has_key = true`**: ✅ Keys are saved

### Check Bot Status:

```sql
SELECT 
    id,
    name,
    connector,
    health_status,
    health_message
FROM bots
WHERE id = 'YOUR_BOT_ID';
```

**If `health_message` is NULL or empty**: ✅ Bot found credentials

---

## Troubleshooting

### If Error Persists After Adding Keys:

1. **Check Exchange Name Match**
   - Bot's `connector` field must match `exchange` in `exchange_credentials`
   - Both are case-insensitive, but check spelling: "coinstore" vs "Coinstore"

2. **Wait 1-2 Minutes**
   - Bot runner checks periodically
   - Health status updates every cycle

3. **Check Bot Logs**
   - Look for: `"✅ Found API keys in exchange_credentials table"`
   - Or: `"⚠️ No credentials found"`

4. **Verify Client ID Match**
   - Credentials must be saved with same `client_id` as bot's owner

---

## Summary

✅ **Don't delete bots** - Use Edit button to add keys  
✅ **Message will disappear** - Within 1-2 minutes after saving  
✅ **100% fix** - Once credentials are saved correctly, error clears automatically  
✅ **No recreation needed** - Existing bots can be fixed in-place

---

## Quick Fix Steps

1. Click **Edit** on bot card
2. Expand **"Add API Keys"**
3. Enter credentials
4. Click **Save**
5. Wait 1-2 minutes
6. Error disappears ✅
