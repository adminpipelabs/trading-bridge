# Proxy 407 Authentication Fix

**Date:** February 10, 2026

---

## 🎯 **Problem**

**Error:** `407 Proxy Authentication Required` from QuotaGuard proxy

**Root Cause:** Proxy URLs were using `https://` but HTTP proxies should use `http://` even when tunneling HTTPS connections.

**Example:**
- ❌ Wrong: `https://user:pass@proxy.com:9294`
- ✅ Correct: `http://user:pass@proxy.com:9294`

---

## ✅ **Fix Applied**

Added proxy URL normalization in multiple places:

1. **`app/cex_volume_bot.py`**
   - Added `normalize_proxy_url()` function
   - Updated `extract_proxy_url_from_quotaguard_info()` to normalize URLs

2. **`app/coinstore_connector.py`**
   - Normalize proxy URL in `__init__()` method

3. **`app/main.py`**
   - Normalize proxy URL before setting `HTTP_PROXY` and `HTTPS_PROXY` env vars

4. **`app/bot_runner.py`**
   - Normalize proxy URLs in both CEX bot and spread bot sections

---

## 🔧 **How It Works**

The fix automatically converts `https://` to `http://` in proxy URLs:

```python
if proxy_url.startswith('https://'):
    proxy_url = 'http://' + proxy_url[8:]  # Replace https:// with http://
```

**Why this works:**
- HTTP proxies use HTTP protocol for the proxy connection itself
- Even when tunneling HTTPS traffic, the proxy connection is HTTP
- Using `https://` causes aiohttp to fail with 407 errors

---

## 📊 **Expected Result**

After deployment:
- ✅ Coinstore API calls should work (no more 407 errors)
- ✅ Proxy authentication should succeed
- ✅ Balance fetching should work for Coinstore bots

---

## 🚨 **Remaining Issue**

**BitMart API Error** - Still needs fixing:
- Error: `bitmart GET https://api-cloud.bitmart.com/account/v1/currencies` failing
- Likely causes: IP whitelist or API key permissions

---

## 📝 **Next Steps**

1. **Deploy to Railway** - The fix is ready
2. **Monitor logs** - Check if 407 errors are gone
3. **Fix BitMart** - Address IP whitelist/API key issues
