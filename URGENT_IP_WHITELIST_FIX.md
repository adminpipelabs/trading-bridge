# 🚨 URGENT: IP Whitelist Mismatch Found!

## Problem Identified

**Coinstore API Key IP Whitelist:** `3.222.129.4`  
**Railway Actual Outbound IP:** `54.205.35.75`  
**Result:** 1401 Unauthorized (IP not whitelisted)

## ✅ Permissions Are Correct
- Read: ✅ Enabled
- Trade: ✅ Enabled  
- Status: ✅ Valid

## ❌ IP Whitelist Mismatch

The API key is configured for `3.222.129.4`, but Railway is using `54.205.35.75`.

## 🛠️ Fix: Add Both IPs to Whitelist

### Option 1: Add Both IPs (Recommended)

1. Go to Coinstore API Key Management
2. Edit API Key: `42b5c7c40bf625e7fcffd16a654b6ed0`
3. Update IP whitelist to include **BOTH**:
   - `3.222.129.4` (already there)
   - `54.205.35.75` (add this one)

4. Save changes
5. Wait 1-2 minutes
6. Test again

### Option 2: Disable IP Whitelist (If Allowed)

If Coinstore allows disabling IP whitelist:
1. Edit API key
2. Disable IP whitelist restriction
3. Save changes
4. Test again

## Why Railway Uses Different IPs

Railway uses QuotaGuard proxy which alternates between:
- `3.222.129.4`
- `54.205.35.75`

Both IPs need to be whitelisted for consistent access.

## Expected Result

After adding `54.205.35.75` to whitelist:
- ✅ Balance fetch will succeed
- ✅ Dashboard will show balances
- ✅ 1401 error will disappear

## Verification

After making changes, check Railway logs - you should see:
- ✅ Successful balance fetch
- ✅ No more 1401 errors
- ✅ Balances displayed on dashboard
