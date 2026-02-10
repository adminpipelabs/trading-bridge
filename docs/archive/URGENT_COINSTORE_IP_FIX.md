# 🚨 URGENT: Coinstore IP Whitelist Fix

## Problem

**Railway logs show:** Railway is using IP `3.222.129.4`  
**Coinstore API key is whitelisted for:** `54.205.35.75`  
**Result:** `1401 Unauthorized` error - IP mismatch!

---

## Root Cause

QuotaGuard proxy alternates between two IPs:
- **Primary IP:** `3.222.129.4` ← **Railway is using this one**
- **Backup IP:** `54.205.35.75` ← Coinstore key is whitelisted for this

Coinstore only allows **1 IP per API key**, so we need to whitelist the IP that Railway is actually using.

---

## Immediate Fix Required

**ACTION:** Change Coinstore API key IP whitelist BACK to: `3.222.129.4`

### Step-by-Step Instructions:

1. **Log into Coinstore Dashboard**
   - Go to: https://www.coinstore.com/ (or your Coinstore account portal)
   - Navigate to API Key Management

2. **Find the API Key**
   - Look for API key starting with: `42b5c7c4...6ed0`
   - Or find the key associated with the trading bot account

3. **Edit IP Whitelist**
   - Click "Edit" or "Settings" on the API key
   - Find "IP Whitelist" or "Allowed IPs" section
   - **Remove:** `54.205.35.75`
   - **Add:** `3.222.129.4`
   - Save changes

4. **Verify**
   - Confirm IP whitelist now shows: `3.222.129.4`
   - Wait 1-2 minutes for changes to propagate

### Why This Fixes It:
- Railway logs show: `🌐 RAILWAY OUTBOUND IP: 3.222.129.4`
- Coinstore currently whitelisted for: `54.205.35.75` (wrong IP)
- Result: `1401 Unauthorized` error
- After fix: IP matches → authentication succeeds → balances load

---

## Long-term Solution (Optional)

If QuotaGuard continues to alternate between IPs, we have two options:

### Option 1: Whitelist Both IPs (if Coinstore supports it)
- Check if Coinstore allows multiple IPs per key
- If yes, whitelist both: `3.222.129.4` and `54.205.35.75`

### Option 2: Configure QuotaGuard to Use Single IP
- Contact QuotaGuard support
- Request configuration to use only `3.222.129.4` consistently
- This prevents IP rotation issues

---

## Verification

After changing IP whitelist to `3.222.129.4`:
1. Wait 1-2 minutes for changes to propagate
2. Check Railway logs for balance fetch
3. Look for: `✅ Coinstore balance API response: code=0` (success)
4. Dashboard should show actual balances instead of zeros

---

## Current Status

- ✅ Code fix deployed (using `json=` parameter for proper Content-Type)
- ❌ IP whitelist mismatch (needs to be `3.222.129.4`)
- ⏳ Waiting for IP whitelist update

---

**Priority:** 🔴 **CRITICAL** - Blocks all Coinstore balance fetching
