# URGENT: Fix Proxy for Coinstore & BitMart

**Date:** February 10, 2026  
**Priority:** 🔴 CRITICAL - Blocking both Coinstore and BitMart

---

## 🎯 **The Problem**

**1401 Unauthorized** from Coinstore because:
- Coinstore API key `42b5c7c40bf625e7fcffd16a654b6ed0` has IP **54.205.35.75** whitelisted
- Without proxy, Railway uses a different IP → 1401 error
- Proxy is broken (407 authentication error)

**Both Coinstore and BitMart need the proxy working.**

---

## ✅ **The Fix**

**ONE simple change in Railway:**

1. Go to Railway Dashboard → trading-bridge service → Variables
2. Find `QUOTAGUARDSTATIC_URL`
3. Change `https://` to `http://`

**Current (WRONG):**
```
https://3o3v9ac4vndm51:6gwp6zf4ovvn26szxayju6jlgtve@us-east-shield-03.quotaguard.com:9294
```

**Should be (CORRECT):**
```
http://3o3v9ac4vndm51:6gwp6zf4ovvn26szxayju6jlgtve@us-east-shield-03.quotaguard.com:9294
```

**That's it. Just change `https://` to `http://`**

---

## 📊 **Why This Fixes It**

- **Coinstore:** Needs proxy to use whitelisted IP 54.205.35.75
- **BitMart:** Needs proxy for IP whitelisting
- **Proxy:** HTTP proxies use `http://` even for HTTPS targets

---

## 🚀 **After Fix**

1. Railway will auto-redeploy
2. Coinstore bots will work (using whitelisted IP via proxy)
3. BitMart bots will work (using proxy for IP whitelist)

---

## ✅ **Verification**

After fix, test:
```bash
curl https://trading-bridge-production.up.railway.app/test/coinstore
```

Should show:
- ✅ Status 200
- ✅ Balance response (not 1401)
- ✅ Proxy test: success

---

**Status:** Code is ready, just needs Railway env var fix.
