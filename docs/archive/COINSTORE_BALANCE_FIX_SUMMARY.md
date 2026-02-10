# Coinstore Balance Fetching - Fix Summary & Next Steps

## 🎯 **What We're Trying To Do**
Fix Coinstore bot balance fetching so that client bots can display their Available/Locked/Volume balances correctly in the UI.

## 📍 **Where We Are Now**

### **Problem Identified:**
1. **Coinstore API Implementation Was Completely Wrong:**
   - ❌ Wrong signature algorithm (was using single HMAC, should be two-step)
   - ❌ Wrong endpoints (`/api/v1/account/balance` → should be `/spot/accountList`)
   - ❌ Wrong headers (`X-API-KEY` → should be `X-CS-APIKEY`, `X-CS-SIGN`, `X-CS-EXPIRES`)
   - ❌ Wrong base URL (was `https://api.coinstore.com` → should be `https://api.coinstore.com/api`)
   - ❌ Wrong response parsing (was expecting dict, actually returns list with AVAILABLE/FROZEN types)

2. **Client API Keys Not Being Loaded:**
   - ❌ `sync_connectors_to_exchange_manager` only checked `exchange_credentials` table if `connectors` table was empty
   - ❌ This meant client-added API keys (in `exchange_credentials`) were ignored if admin had added any connectors

### **Fixes Applied:**
1. ✅ **Completely rewrote Coinstore API implementation** (`app/coinstore_connector.py`, `app/coinstore_adapter.py`):
   - Fixed signature algorithm to match official docs (two-step HMAC-SHA256)
   - Fixed all endpoints to match official API
   - Fixed headers and authentication
   - Fixed response parsing for balance (handles list format with type 1=AVAILABLE, type 4=FROZEN)

2. ✅ **Fixed connector sync logic** (`app/api/client_data.py`):
   - Now ALWAYS checks `exchange_credentials` table, regardless of `connectors` table
   - Ensures client API keys are always loaded

3. ✅ **Added better error handling** (`app/coinstore_adapter.py`, `app/coinstore_connector.py`):
   - Better error messages (no more "API error: None")
   - Detailed logging of API responses
   - Handles HTTP errors and non-JSON responses

### **Current Status:**
- ✅ Code changes committed and pushed to GitHub
- ✅ Railway should auto-deploy
- ⏳ **NEED TO TEST:** Coinstore balance fetching hasn't been tested yet with new implementation

## 🎯 **Outcome We Want**

### **Success Criteria:**
1. ✅ Coinstore bots can fetch balances successfully
2. ✅ Client dashboard shows correct balances:
   - `Available: X SHARP | Y USDT`
   - `Locked: X SHARP | Y USDT`
   - `Volume: $X` (for Volume bots) or `Buy/Sell: X buys, Y sells` (for Spread bots)
3. ✅ No more "API error: None" or "user-not-login" errors
4. ✅ Coinstore API calls succeed with proper authentication

### **Expected Log Output (Success):**
```
✅ Synced connector coinstore from exchange_credentials to exchange_manager
Fetching balance from coinstore for pair SHARP/USDT
Coinstore balance API response: code=0, data type=<class 'list'>
✅ Successfully parsed balances: SHARP available=X, locked=Y; USDT available=X, locked=Y
```

### **What To Check If It Fails:**
1. **Check Railway logs for Coinstore API calls:**
   - Look for: `Coinstore API POST /spot/accountList response status=...`
   - Check if status is 200 or error code
   - Check response body for error messages

2. **Check signature/authentication:**
   - Error 401 = authentication failed (signature wrong or API keys invalid)
   - Error 404 = endpoint wrong (shouldn't happen with new code)
   - Error 500 = Coinstore server error

3. **Check connector sync:**
   - Look for: `✅ Synced connector coinstore from exchange_credentials`
   - If missing, check if API keys exist in `exchange_credentials` table for the client

## 🔍 **Debugging Steps If Needed**

### **1. Verify API Keys Are Saved:**
```sql
SELECT client_id, exchange, created_at 
FROM exchange_credentials 
WHERE exchange = 'coinstore';
```

### **2. Check Connector Sync:**
Look for logs like:
```
🔄 Syncing connectors for account: client_new_sharp_foundation
✅ Found 2 credential(s) in 'exchange_credentials' table
✅ Synced connector coinstore from exchange_credentials to exchange_manager
```

### **3. Test Balance Endpoint Directly:**
Call `GET /bots/{bot_id}/balance-and-volume` for a Coinstore bot and check:
- Does it return balance data?
- What error message if it fails?
- Check Railway logs for the actual Coinstore API response

### **4. Verify Signature Algorithm:**
If getting 401 errors, verify signature matches Coinstore's requirements:
- Step 1: `HMAC-SHA256(secret_key, floor(expires/30000))` → key
- Step 2: `HMAC-SHA256(key, payload)` → signature
- Headers: `X-CS-APIKEY`, `X-CS-SIGN`, `X-CS-EXPIRES`

## 📝 **Files Changed**
- `app/coinstore_connector.py` - Complete rewrite of API client
- `app/coinstore_adapter.py` - Fixed balance parsing and error handling
- `app/api/client_data.py` - Fixed connector sync to always check exchange_credentials
- `app/services/exchange.py` - Added BitMart error handler workaround
- `app/bot_routes.py` - Added better logging for connector debugging

## 🔧 **BitMart Proxy Fix (Already Applied ✅)**

### **Status:**
✅ BitMart proxy is already using `aiohttp_proxy` correctly in `app/cex_volume_bot.py` (line 236).

### **If BitMart Still Has Issues:**
The proxy fix is in place, but BitMart API is currently returning "Internal Server Error" (code 59002). This is a BitMart server-side issue, not our code. However, if you see "IP forbidden" errors (error 30010), verify:
- ✅ Railway IP `3.222.129.4` is whitelisted on BitMart API key
- ✅ Proxy is being used correctly (check logs for `✅ Proxy configured (aiohttp_proxy)`)

## 🚨 **Known Issues (Not Related to Coinstore)**
- BitMart API returning "Internal Server Error" (code 59002) - This is BitMart's server issue, not our code
- Some bots failing to start due to database transaction errors (separate issue)

## ❓ **Questions for Dev**
1. **If Coinstore still fails after this fix:**
   - Can you check Railway logs for the actual Coinstore API response?
   - What error code/message is Coinstore returning?
   - Are the API keys definitely valid and have the right permissions?

2. **If signature authentication fails:**
   - Can you verify the API keys are correct?
   - Are there any IP whitelist restrictions on the Coinstore API keys?
   - Should we test with a simple Python script first to verify signature works?

3. **If balance parsing fails:**
   - Can you share a sample Coinstore balance API response?
   - Does the response format match what we're expecting (list with AVAILABLE/FROZEN types)?

## ✅ **Quick Test Checklist After Deploy**

| Check | Expected Log | What It Means |
|-------|-------------|---------------|
| **Coinstore auth** | `Coinstore API POST /spot/accountList response status=200` | ✅ Authentication successful |
| **Coinstore balance** | `Available: X SHARP \| Y USDT` | ✅ Balance parsing works |
| **BitMart auth** | No `error 30010` (IP forbidden) | ✅ Proxy working correctly |
| **BitMart balance** | Successful balance fetch | ✅ BitMart connection works |

### **If Coinstore Still Fails with Auth Errors:**

The two-step signature might need debugging. Add logging to `app/coinstore_connector.py` in `_generate_signature` method:

```python
def _generate_signature(self, expires: int, payload: str) -> str:
    import math
    
    # Step 1: Calculate expires_key
    expires_key = str(math.floor(expires / 30000))
    logger.info(f"🔍 Coinstore signature debug - expires: {expires}, expires_key: {expires_key}")
    
    # Step 2: First HMAC to get key
    key = hmac.new(
        self.api_secret.encode('utf-8'),
        expires_key.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    logger.info(f"🔍 Coinstore signature debug - key: {key[:20]}...")
    
    # Step 3: Second HMAC to get signature
    signature = hmac.new(
        key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    logger.info(f"🔍 Coinstore signature debug - signature: {signature[:20]}...")
    logger.info(f"🔍 Coinstore signature debug - payload length: {len(payload)}")
    
    return signature
```

This will help verify:
- ✅ `expires_key` calculation is correct (should be `floor(expires/30000)`)
- ✅ Signature generation matches Coinstore's expected format
- ✅ Payload is being signed correctly

## ✅ **Next Steps**
1. Wait for Railway deployment to complete
2. Test Coinstore balance fetching from client dashboard
3. Test BitMart balance fetching (should work after proxy fix)
4. Check Railway logs using the test checklist above
5. If errors persist, add signature debugging logs and share with Dev
