# Message for CTO - Coinstore Fix

**Date:** February 10, 2026

---

## 🎯 **Two Issues Found**

### **1. Wrong API Key Being Used** ❌

**Problem:** Test endpoint used API key `e1f00e7f40...ef931` but Coinstore key should be `42b5c7c40bf625e7fcffd16a654b6ed0`

**Fix Applied:** Updated database query to get correct Coinstore credentials from running Coinstore bots

**Status:** ✅ Fixed in code

---

### **2. Proxy URL Wrong** ❌

**Problem:** `QUOTAGUARDSTATIC_URL` in Railway env vars uses `https://` but should be `http://`

**Fix Needed:** Update Railway environment variable:
- Current: `https://3o3v9ac4vndm51:6gwp6zf4ovvn26szxayju6jlgtve@us-east-shield-03.quotaguard.com:9294`
- Should be: `http://3o3v9ac4vndm51:6gwp6zf4ovvn26szxayju6jlgtve@us-east-shield-03.quotaguard.com:9294`

**Action:** Change `QUOTAGUARDSTATIC_URL` in Railway → Variables → Change `https://` to `http://`

**Status:** ⚠️ Needs manual fix in Railway dashboard

---

## ✅ **Additional Fix: Bypass Proxy for Coinstore**

**Finding:** Coinstore API works WITHOUT proxy (test confirmed - request reached API)

**Fix Applied:** Updated `app/coinstore_connector.py` to bypass proxy for Coinstore calls

**Why:** Coinstore doesn't require IP whitelisting, so proxy is unnecessary and was causing timeouts

**Status:** ✅ Fixed in code

---

## 📊 **Summary**

**Fixed:**
- ✅ Correct API key selection
- ✅ Bypass proxy for Coinstore

**Needs Manual Fix:**
- ⚠️ Update `QUOTAGUARDSTATIC_URL` in Railway: `https://` → `http://`

**Result After Fixes:**
- Coinstore should work (no proxy, correct key)
- BitMart still needs proxy (for IP whitelist) - will work once proxy URL is fixed

---

## 🚀 **Next Steps**

1. **Redeploy** - Code fixes are pushed
2. **Fix Railway env var** - Change `QUOTAGUARDSTATIC_URL` from `https://` to `http://`
3. **Test** - Call `/test/coinstore` endpoint to verify it works
4. **Monitor logs** - Check if Coinstore bots start placing orders
