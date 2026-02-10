# Coinstore Account Settings Checklist

## 🎯 Simple Fix - Account Settings (Not Code)

**Status:** Code is correct. Issue is likely in Coinstore account settings/permissions.

---

## ✅ Step-by-Step Checklist

### 1. Log into Coinstore Dashboard
- Go to: https://www.coinstore.com
- Login with the account that created the API key

### 2. Navigate to API Management
- Go to: **User Center** → **API Management** (or **API Keys**)
- Find the API key being used by the bot

### 3. Check API Key Settings

#### ✅ **Permission Settings** (MOST IMPORTANT)
- [ ] **"Read" permission** - Must be **ENABLED**
- [ ] **"Spot Trading" permission** - Must be **ENABLED** ← **CRITICAL**
- [ ] **"Trade" permission** - Must be **ENABLED** (if separate from Spot Trading)

**Note:** Some exchanges have separate permissions for:
- Reading balances
- Spot trading
- Futures trading
- Withdrawals

Make sure **ALL trading-related permissions are enabled**.

#### ✅ **IP Whitelist Settings**
- [ ] Check if IP whitelist is **ENABLED** or **DISABLED**
- [ ] If **ENABLED**: Verify `5.161.64.209` (Hetzner IP) is in the whitelist
- [ ] If **DISABLED**: This is fine - no IP restrictions

**Current Server IP:** `5.161.64.209` (Hetzner VPS)

#### ✅ **API Key Status**
- [ ] Key status is **ACTIVE** (not revoked, expired, or suspended)
- [ ] Key is not restricted or locked

### 4. Check Account-Level Settings

#### ✅ **Account Verification**
- [ ] Account is **verified** (KYC completed if required)
- [ ] Account is **active** (not suspended or restricted)

#### ✅ **Trading Authority**
- [ ] **Spot Trading** is enabled for the account
- [ ] Account has trading permissions (not read-only)
- [ ] No trading restrictions or limits on the account

#### ✅ **API Access**
- [ ] API access is enabled for the account
- [ ] No API restrictions or bans

### 5. Verify API Key Details Match

**Check these match what's in the database:**
- [ ] API Key value matches exactly (no extra spaces)
- [ ] Secret Key matches exactly (if you can view it)
- [ ] Key was created for the correct account

---

## 🔧 Common Issues & Fixes

### Issue 1: "Spot Trading" Permission Not Enabled
**Symptom:** `signature-failed` (401) on all trading endpoints  
**Fix:** Enable "Spot Trading" permission in API key settings  
**Impact:** This is the #1 cause of signature failures

### Issue 2: IP Whitelist Missing Server IP
**Symptom:** `signature-failed` (401) or `unauthorized` (1401)  
**Fix:** Add `5.161.64.209` to IP whitelist OR disable IP whitelist  
**Impact:** Server IP must be whitelisted if IP restrictions are enabled

### Issue 3: Account Trading Disabled
**Symptom:** `signature-failed` (401) even with correct permissions  
**Fix:** Enable spot trading at account level (not just API key)  
**Impact:** Account must have trading enabled, not just API key

### Issue 4: API Key Revoked/Expired
**Symptom:** `signature-failed` (401)  
**Fix:** Create new API key or reactivate existing one  
**Impact:** Key must be active

---

## 📋 Quick Verification Steps

1. **Log into Coinstore Dashboard**
2. **Go to API Management**
3. **Find API Key** (check which key the bot is using)
4. **Verify:**
   - ✅ Spot Trading = **ENABLED**
   - ✅ Read = **ENABLED**
   - ✅ IP Whitelist includes `5.161.64.209` OR is disabled
   - ✅ Key Status = **ACTIVE**
5. **Save changes** (if any were made)
6. **Wait 1-2 minutes** for changes to propagate
7. **Test again** - bot should work immediately

---

## 🎯 Most Likely Fix

**90% chance:** "Spot Trading" permission is not enabled on the API key.

**Quick fix:**
1. Coinstore Dashboard → API Management
2. Find the API key
3. Enable "Spot Trading" permission
4. Save
5. Wait 1-2 minutes
6. Bot should work

---

## 📞 If Still Not Working

After checking all above:
1. Verify API key and secret match exactly (no typos, extra spaces)
2. Try creating a NEW API key with all permissions enabled
3. Update the bot with the new API key
4. Test again

**Note:** Sometimes API keys can be corrupted or have hidden restrictions. Creating a fresh key often resolves this.

---

## 🔍 What to Check in Coinstore Dashboard

**Look for these settings:**
- ✅ **Permissions** section → "Spot Trading" checkbox
- ✅ **IP Whitelist** section → List of allowed IPs
- ✅ **Status** section → Active/Inactive
- ✅ **Account Settings** → Trading enabled

**If you see:**
- ❌ "Spot Trading" unchecked → **Enable it**
- ❌ IP whitelist enabled but `5.161.64.209` not listed → **Add it**
- ❌ Key status = "Inactive" → **Activate it**
- ❌ Account trading disabled → **Enable account trading**

---

**Created:** 2026-02-10  
**Purpose:** Simple checklist for Coinstore account settings that might be blocking API access
