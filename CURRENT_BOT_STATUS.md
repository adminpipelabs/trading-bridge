# Current Bot Status & Blockers

**Last Updated:** 2026-02-09

## 🚦 **Current Blockers**

| Bot | Exchange | Type | Blocker | Fix Status | Notes |
|-----|----------|------|---------|------------|-------|
| Sharp-SB-BitMart | BitMart | Spread | ⚠️ Logic not implemented | 🔴 Blocked | "Spread bot logic not yet implemented" |
| Sharp-VB-BitMart | BitMart | Volume | Error 59002 + Low USDT | ⏳ Out of our control | BitMart server error; Only 1.66 USDT (need $5+ for orders) |
| SHARP-SB-Coinstore | Coinstore | Spread | ⚠️ Logic not implemented | 🔴 Blocked | "Spread bot logic not yet implemented" |
| SHARP-VB-Coinstore | Coinstore | Volume | ❌ Not running | 🔍 **NEEDS START** | Not in running bots list - needs to be started |

## ✅ **Fixes Deployed**

1. **Coinstore API Implementation** ✅
   - Fixed signature algorithm (two-step HMAC-SHA256)
   - Fixed endpoints (`/spot/accountList`)
   - Fixed headers (`X-CS-APIKEY`, `X-CS-SIGN`, `X-CS-EXPIRES`)
   - Fixed base URL (`https://api.coinstore.com/api`)
   - Fixed response parsing (handles list format)

2. **Connector Sync Logic** ✅
   - Now always checks `exchange_credentials` table
   - Client API keys are always loaded

3. **BitMart Proxy** ✅
   - Already using `aiohttp_proxy` correctly
   - Proxy is configured properly

## 📋 **Next Steps**

| Issue | Status | Who | Action |
|-------|--------|-----|--------|
| DB transaction errors | ✅ Fixed | Dev | Deployed, should unblock bot startup |
| Coinstore balance fetch | 🧪 Ready to test | After deploy | Hit "Retry" on Coinstore bot, check if balances show |
| BitMart IP whitelist | 🔴 **URGENT** | User | Add `54.205.35.75` in BitMart dashboard (proxy rotating between 2 IPs) |

### **Immediate Actions:**

1. ⏳ **Wait for Railway deployment** (~1-2 minutes)
2. 🧪 **Test Coinstore bots:**
   - Open client dashboard
   - Click "Retry" on a Coinstore bot balance display
   - Check if balances show: `Available: X SHARP | Y USDT`
   - Verify Railway logs show: `Coinstore API POST /spot/accountList response status=200`
3. 🔧 **BitMart IP whitelist:**
   - Go to BitMart API settings → IP whitelist
   - Add `54.205.35.75` (both `3.222.129.4` and `54.205.35.75` should be whitelisted)
   - This will fix BitMart "IP forbidden" errors

## 🎯 **Success Criteria**

### Coinstore Bots:
- ✅ Balance displays: `Available: X SHARP | Y USDT`
- ✅ No "API error: None" or "user-not-login" errors
- ✅ Logs show: `Coinstore API POST /spot/accountList response status=200`

### BitMart Bots:
- ✅ No error 59002 (BitMart server issue)
- ✅ Successful balance fetch
- ✅ Trades execute successfully

## 📊 **Test Checklist After Deploy**

| Check | Expected Result | Status |
|-------|----------------|--------|
| Coinstore auth | `status=200` in logs | ⏳ Pending |
| Coinstore balance | Shows in UI | ⏳ Pending |
| BitMart auth | No IP forbidden errors | ✅ Already working |
| BitMart balance | Fetches successfully | ⏳ Blocked by server error |

## 🔍 **Monitoring**

Watch Railway logs for:
- Coinstore API calls and responses
- BitMart error 59002 frequency
- Any new authentication errors
- Balance fetch success/failure

## 📝 **Notes**

### **BitMart IP Forbidden (Error 30010) - Quick Fix** ✅ CONFIRMED
- **Clarification:** Those IPs (`3.222.129.4` and `54.205.35.75`) are **QuotaGuard proxy IPs**, not Railway IPs
- **This means:** ✅ Proxy IS working correctly! BitMart is seeing the QuotaGuard IPs
- **Confirmed:** Proxy is **rotating between two QuotaGuard IPs** (load balanced)
- **Solution:** Whitelist **both** QuotaGuard IPs on BitMart API key:
  - `3.222.129.4` ✅ (probably already whitelisted)
  - `54.205.35.75` ← **CRITICAL: Add this one now** (confirmed rotating IP)
- **Why:** QuotaGuard uses both IPs (load balanced), so both need to be whitelisted
- **Action:** Go to BitMart API settings → IP whitelist → Add `54.205.35.75`

### **Coinstore Fix**
- Complete rewrite based on official API documentation
- Should resolve all authentication and balance fetching issues
- **Status:** Fix deployed but bots failed to start due to database transaction errors
- **Action needed:** Fix database transaction errors preventing bot startup

### **Database Transaction Errors** ✅ FIXED
- **Problem:** Multiple bots failing to start: `InFailedSqlTransaction`
- **Root cause:** SQL query fails (exchange/chain columns don't exist) → transaction aborted → subsequent queries fail
- **Fix applied:**
  - Added `db.rollback()` in `bot_runner.py` when exchange/chain query fails
  - Added try-except wrapper around each bot startup to isolate failures
  - Each bot startup is now isolated - one failure won't break others
- **Status:** ✅ Fix deployed - **All 3 bots started successfully!**

### **Current Bot Status (From Latest Logs)**

**✅ Working:**
- Proxy working → **Rotating between two QuotaGuard IPs:**
  - `3.222.129.4` ✅
  - `54.205.35.75` ✅ (confirmed in latest logs)
- BitMart auth working → Balance fetch successful
- BitMart balance: `8,364,285 SHARP` | `1.66 USDT`
- All bots started successfully (no more transaction errors)

**❌ Issues:**
- **BitMart orders:** Error 59002 "Internal Server Error" - BitMart server-side issue
- **Low USDT:** Only 1.66 USDT (min order is 5 USDT) - can only sell, not buy
- **Spread bots:** "⚠️ Spread bot logic not yet implemented"
- **Coinstore bots:** `SHARP-SB-Coinstore` started but no balance fetch attempts in logs yet

**Action Items:**

1. 🚀 **Start SHARP-VB-Coinstore** (CRITICAL - needed to test Coinstore fix):
   ```sql
   UPDATE bots SET status = 'running' WHERE name = 'SHARP-VB-Coinstore';
   ```
   OR start it from the dashboard UI
   
2. 🧪 **Test Coinstore balance** - Once `SHARP-VB-Coinstore` is running:
   - Click "Retry" on `SHARP-VB-Coinstore` in dashboard to trigger balance fetch
   - Check Railway logs for: `Coinstore API POST /spot/accountList response status=200`
   - Verify balances show: `Available: X SHARP | Y USDT`

3. ✅ **Add USDT to BitMart** - Need at least $10-20 to enable buy orders

4. ⏳ **Wait/retry BitMart** - 59002 is their internal error, may resolve itself

**Note:** Spread bots (`SHARP-SB-Coinstore`, `Sharp-SB-BitMart`) cannot test Coinstore because spread bot logic is not implemented yet. Only volume bots can test the Coinstore connector.
