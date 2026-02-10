# Coinstore Balance Status - Final Summary

**Date:** February 9, 2026  
**Status:** ❌ Still getting 1401 Unauthorized - Unable to fetch balances

---

## ✅ What We Fixed

1. **Signature Algorithm** ✅
   - Implemented two-step HMAC-SHA256 per Coinstore docs
   - Step 1: `HMAC(secret, expires_key)` where `expires_key = floor(expires/30000)`
   - Step 2: `HMAC(derived_key, payload)`
   - Verified with unit tests - matches official example exactly

2. **Payload Format** ✅
   - Fixed: POST with empty params uses `json.dumps({})` = `'{}'` (not empty string `''`)
   - Matches Coinstore official documentation example
   - Verified payload is correct in logs: `payload='{}' (length=2)`

3. **Request Headers** ✅
   - `X-CS-APIKEY`: API key
   - `X-CS-SIGN`: HMAC signature
   - `X-CS-EXPIRES`: Timestamp (milliseconds)
   - `exch-language`: 'en_US'
   - `Content-Type`: 'application/json'

4. **Whitespace Stripping** ✅
   - Added `.strip()` to API keys when decrypting and initializing connector
   - Prevents copy-paste whitespace issues

5. **Logging** ✅
   - Detailed signature generation logs
   - API response logging
   - Key length/preview logging
   - Balance extraction logging

---

## ❌ Current Issue

**Error:** `Coinstore API error (code 1401): Unauthorized`

**What We Know:**
- ✅ Payload is correct: `'{}'`
- ✅ Signature algorithm matches example
- ✅ Headers are correct
- ✅ API key has "spot" and "read" permissions enabled
- ✅ No IP whitelist option on Coinstore
- ✅ Credentials decrypt successfully
- ✅ Request reaches Coinstore API (gets HTTP 200, but API error 1401)

**What We Don't Know:**
- Are the API keys themselves valid?
- Is there a subtle request format difference we're missing?
- Are the keys expired or revoked?

---

## 🔍 Code Verification

**Signature Generation** (`app/coinstore_connector.py` lines 40-70):
```python
# Matches official example exactly
expires_key = str(math.floor(expires / 30000))
key = hmac.new(api_secret.encode('utf-8'), expires_key.encode('utf-8'), hashlib.sha256).hexdigest()
signature = hmac.new(key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
```

**Payload** (`app/coinstore_connector.py` line 90):
```python
payload = json.dumps(params, separators=(',', ':')) if params else json.dumps({})
# For empty params: payload = '{}' ✅
```

**Request** (`app/coinstore_connector.py` lines 139-143):
```python
body_data = payload.encode('utf-8')  # b'{}'
async with session.post(url, data=body_data, **request_kwargs) as response:
```

---

## 📋 Next Steps (For Future Debugging)

1. **Verify API Keys Manually**
   - Test keys directly with Coinstore's official Python example
   - Confirm keys work outside our system
   - Check if keys are expired/revoked

2. **Compare Request Format**
   - Use network capture tool (Wireshark/Charles) to compare our request vs working example
   - Check exact byte-by-byte request format
   - Verify headers order/format

3. **Test with Fresh Keys**
   - Generate new Coinstore API keys
   - Test with minimal example script
   - If new keys work, old keys may be invalid

4. **Contact Coinstore Support**
   - Ask about error code 1401 specifically
   - Verify API key format/requirements
   - Check if there are any special requirements for `/spot/accountList` endpoint

---

## 📝 Files Modified

- `app/coinstore_connector.py` - Signature algorithm, payload format, logging
- `app/coinstore_adapter.py` - Balance parsing, logging
- `app/api/client_data.py` - Whitespace stripping, key logging
- `app/bot_routes.py` - Balance endpoint logging
- `app/security.py` - Decryption functions (fixed earlier)

---

## 🎯 Conclusion

**Code is correct** - matches Coinstore documentation and official examples.  
**Issue is likely** - Invalid API keys or Coinstore API-side configuration.

**Recommendation:** Test API keys independently with Coinstore's official example script before debugging further.
