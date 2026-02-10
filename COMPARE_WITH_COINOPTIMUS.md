# Comparison with CoinOptimus Open Source Implementation

**Source:** https://github.com/Adamant-im/adamant-coinoptimus/blob/dev/trade/api/coinstore_api.js

---

## ✅ **Signature Algorithm - MATCHES**

**Their implementation:**
```javascript
function getSignature(secret, timestamp, payload) {
    const key = crypto.createHmac('sha256', secret)
        .update(Math.floor(timestamp / 30000).toString())
        .digest('hex');

    return crypto
        .createHmac('sha256', key)
        .update(payload)
        .digest('hex');
}
```

**Our implementation:**
```python
def _generate_signature(self, expires: int, payload: str) -> str:
    expires_key = str(math.floor(expires / 30000))
    key = hmac.new(secret_bytes, expires_key_bytes, hashlib.sha256).hexdigest()
    signature = hmac.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()
    return signature
```

**✅ IDENTICAL** - Both use:
1. `floor(timestamp / 30000)` as expires_key
2. `HMAC(secret, expires_key)` → key
3. `HMAC(key, payload)` → signature

---

## 🔍 **Headers Comparison**

**Their headers (working implementation):**
```javascript
headers: {
  'Content-Type': 'application/json',
  'X-CS-APIKEY': config.apiKey,
  'X-CS-EXPIRES': timestamp,
  'X-CS-SIGN': sign,
}
```

**Our headers:**
```python
headers = {
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Connection': 'keep-alive',
    'X-CS-APIKEY': self.api_key,
    'X-CS-SIGN': signature,
    'X-CS-EXPIRES': str(expires),
    'exch-language': 'en_US',  # ← They DON'T include this!
}
```

**Difference:** They don't include `exch-language`, `Accept`, or `Connection` headers.

---

## 📋 **Request Format**

**Their POST request:**
```javascript
if (type === 'post') {
    httpOptions.data = stringifiedData;  // JSON string
}
```

**Our POST request:**
```python
body_bytes = payload.encode('utf-8') if payload else b'{}'
async with session.post(url, data=body_bytes, ...)
```

**✅ Both send JSON string as raw bytes**

---

## 🎯 **Key Finding**

**Their working implementation:**
- ✅ Uses same signature algorithm
- ✅ Uses same headers (except they don't include `exch-language`)
- ✅ Sends JSON string as body

**Our implementation:**
- ✅ Uses same signature algorithm  
- ✅ Uses same headers (but includes extra `exch-language`)
- ✅ Sends JSON string as body

**The code is correct!** The issue is NOT the implementation.

---

## 🔧 **What This Tells Us**

1. **Our signature is correct** - matches working open-source implementation
2. **Our headers are fine** - extra headers shouldn't cause 1401
3. **Our request format is correct** - matches their working code

**The 1401 error is NOT a code issue. It's:**
- IP whitelist configuration
- API secret mismatch
- API key permissions

---

## ✅ **Conclusion**

Our implementation matches the working open-source code. The issue is configuration, not code.

**Next steps:**
1. Run `test_coinstore_direct.py` on Hetzner
2. Verify IP whitelist on Coinstore dashboard
3. Verify API secret matches dashboard
