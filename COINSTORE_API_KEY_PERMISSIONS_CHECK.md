# Coinstore API Key Permissions Check

**Date:** February 10, 2026  
**Issue:** LIMIT orders return 1401, but MARKET orders work  
**Context:** Other market makers successfully place LIMIT orders on SHARP/USDT

---

## ✅ **Confirmed Facts**

1. **MARKET orders work** → API key has basic trading permission
2. **LIMIT orders fail with 1401** → Application-level rejection
3. **Other market makers place LIMIT orders on SHARP/USDT** → Pair is not restricted
4. **Standalone script also fails** → Not a code issue

---

## 🔍 **What to Check in Coinstore Dashboard**

### 1. **API Key Permissions**

Go to: https://www.coinstore.com/#/user/bindAuth/ManagementAPI

**Check for:**
- ✅ **Read** permission (for balance queries)
- ✅ **Trade** permission (for MARKET orders - already working)
- ❓ **Limit Order** permission (separate toggle?)
- ❓ **Spot Trading** permission
- ❓ **Advanced Trading** permission

**Some exchanges have separate permissions for:**
- Market orders
- Limit orders
- Stop orders
- Advanced order types

### 2. **Account-Level Restrictions**

**Check account settings for:**
- Trading restrictions
- Order type restrictions
- Pair-specific restrictions
- Account verification status

### 3. **IP Whitelist**

**Verify:**
- Current server IP is whitelisted: `5.161.64.209`
- IP whitelist allows all order types (not just MARKET)

---

## 🎯 **Action Items**

1. **Check API Key Permissions:**
   - Log into Coinstore dashboard
   - Go to API Management
   - Find the active API key
   - Check ALL permission toggles
   - Look for any "Limit Order" or "Advanced Trading" options

2. **Compare with Working Setup:**
   - If you have access to another API key that works for LIMIT orders, compare permissions
   - Check if there are any differences

3. **Contact Coinstore Support:**
   - If permissions look correct, contact support
   - Ask why LIMIT orders return 1401 while MARKET orders work
   - Reference: API key ending in `...c7fc9`

---

## 📝 **Current API Key Info**

- **API Key:** `f2f72f8005...c7fc9` (last 5 chars)
- **Server IP:** `5.161.64.209`
- **Status:** MARKET orders ✅, LIMIT orders ❌ (1401)

---

## 🔧 **Possible Solutions**

1. **Enable Limit Order Permission** (if separate toggle exists)
2. **Regenerate API Key** with all permissions enabled
3. **Contact Coinstore Support** to enable LIMIT order trading for this API key
4. **Check Account Verification** - some exchanges restrict LIMIT orders until account is fully verified

---

**Next Step:** Check Coinstore dashboard for API key permissions and report findings.
