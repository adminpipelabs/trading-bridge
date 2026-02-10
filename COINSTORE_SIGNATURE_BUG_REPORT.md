# Coinstore API Signature Authentication Bug Report

## 🚨 Status: CRITICAL BLOCKER

**Issue:** Coinstore API returns `signature-failed` (401) for all authenticated requests (balance checks and order placement).

**Impact:** Bot cannot fetch balances or place trades. All authenticated API calls fail.

**Current State:** Signature generation code matches Coinstore documentation, but API still rejects signatures.

---

## 📋 Problem Summary

The Coinstore Volume Bot is unable to authenticate with the Coinstore API. All authenticated requests return:
```json
{"message": "signature-failed", "code": 401}
```

This affects:
- ✅ Balance fetching (`/spot/accountList`) - FAILS
- ✅ Order placement (`/trade/order/place`) - FAILS
- ✅ Public endpoints (ticker) - WORKS (no auth needed)

---

## 🔍 What We've Verified

### ✅ API Credentials
- API key and secret are loaded correctly
- Credentials are stored in database and loaded via `exchange_manager`
- API key format appears correct (string, no extra whitespace)

### ✅ Signature Generation Implementation
- Matches Coinstore documentation exactly:
  1. Calculate `expires_key = floor(expires / 30000)`
  2. First HMAC: `HMAC-SHA256(secret_key, expires_key)` → `key`
  3. Second HMAC: `HMAC-SHA256(key, payload)` → `signature`
- Payload matches request body exactly
- Timestamp in payload matches `X-CS-EXPIRES` header

### ✅ Request Format
- Headers include: `X-CS-APIKEY`, `X-CS-SIGN`, `X-CS-EXPIRES`, `exch-language`
- Content-Type: `application/json`
- Payload is sent as UTF-8 bytes matching signature calculation

### ✅ IP Whitelisting
- Hetzner server IP: `5.161.64.209`
- IP whitelisting configured on Coinstore dashboard (if required)

---

## 📝 Code Implementation

### Signature Generation (`app/coinstore_connector.py`)

```python
def _generate_signature(self, expires: int, payload: str) -> str:
    """
    Generate HMAC-SHA256 signature for authenticated requests.
    Per Coinstore API docs: https://coinstore-openapi.github.io/en/#signature-authentication
    """
    # Step 1: Calculate expires_key
    expires_key = str(math.floor(expires / 30000))
    
    # Step 2: First HMAC to get derived key
    secret_bytes = self.api_secret.encode('utf-8')
    expires_key_bytes = expires_key.encode('utf-8')
    key_hex = hmac.new(
        secret_bytes,
        expires_key_bytes,
        hashlib.sha256
    ).hexdigest()
    
    # Step 3: Second HMAC to get signature
    key_bytes = key_hex.encode('utf-8')
    payload_bytes = payload.encode('utf-8')
    signature = hmac.new(
        key_bytes,
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    return signature
```

### Request Construction (`app/coinstore_connector.py`)

```python
async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, authenticated: bool = False):
    # Prepare payload
    if method.upper() == 'GET':
        payload = urlencode(params) if params else ''
    else:
        # POST: payload is JSON body
        payload = json.dumps(params, separators=(',', ':')) if params else json.dumps({})
    
    # Generate signature
    if authenticated:
        if params and 'timestamp' in params:
            expires = params['timestamp']
        else:
            expires = int(time.time() * 1000)
        
        signature = self._generate_signature(expires, payload)
        
        headers = {
            'X-CS-APIKEY': self.api_key,
            'X-CS-SIGN': signature,
            'X-CS-EXPIRES': str(expires),
            'exch-language': 'en_US',
            'Content-Type': 'application/json',
        }
    
    # Send request
    body_bytes = payload.encode('utf-8') if payload else b'{}'
    async with session.post(url, data=body_bytes, headers=headers) as response:
        return await response.json()
```

### Order Placement Example

```python
# Payload constructed:
params = {
    'symbol': 'SHARPUSDT',
    'side': 'SELL',
    'ordType': 'MARKET',
    'timestamp': 1770742394290,
    'ordQty': '1386.193512614361'
}

# JSON payload string (for signature):
payload_json = '{"symbol":"SHARPUSDT","side":"SELL","ordType":"MARKET","timestamp":1770742394290,"ordQty":"1386.193512614361"}'

# Headers sent:
{
    'X-CS-APIKEY': '<api_key>',
    'X-CS-SIGN': '<calculated_signature>',
    'X-CS-EXPIRES': '1770742394290',
    'exch-language': 'en_US',
    'Content-Type': 'application/json'
}
```

---

## 📊 Logs from Failed Request

### Balance Check Failure
```
{"timestamp": "2026-02-10T16:53:13.891129", "level": "info", "logger": "app.coinstore_adapter", "message": "💰 Coinstore balance API response: code=401, data type=<class 'NoneType'>"}
{"timestamp": "2026-02-10T16:53:13.891266", "level": "error", "logger": "app.coinstore_adapter", "message": "Coinstore API error: code=401, msg=signature-failed, full response={'message': 'signature-failed', 'code': 401}"}
```

### Order Placement Failure
```
{"timestamp": "2026-02-10T16:53:14.290477", "level": "info", "logger": "app.coinstore_connector", "message": "🔵 PLACING COINSTORE ORDER: endpoint=/trade/order/place, payload={'symbol': 'SHARPUSDT', 'side': 'SELL', 'ordType': 'MARKET', 'timestamp': 1770742394290, 'ordQty': '1386.193512614361'}"}
{"timestamp": "2026-02-10T16:53:14.290524", "level": "info", "logger": "app.coinstore_connector", "message": "🔵 ORDER PAYLOAD JSON (for signature): {\"symbol\":\"SHARPUSDT\",\"side\":\"SELL\",\"ordType\":\"MARKET\",\"timestamp\":1770742394290,\"ordQty\":\"1386.193512614361\"}"}
{"timestamp": "2026-02-10T16:53:14.502625", "level": "info", "logger": "app.coinstore_connector", "message": "🔵 COINSTORE ORDER RESPONSE: {'message': 'signature-failed', 'code': 401}"}
```

---

## 🔬 Comparison with Coinstore Documentation

### Coinstore Python Example (from docs)
```python
import hashlib
import hmac
import json
import math
import time
import requests

url = "https://api.coinstore.com/api/spot/accountList"
api_key = b'your api_key'
secret_key = b'your secret_key'
expires = int(time.time() * 1000)
expires_key = str(math.floor(expires / 30000))
expires_key = expires_key.encode("utf-8")
key = hmac.new(secret_key, expires_key, hashlib.sha256).hexdigest()
key = key.encode("utf-8")
payload = json.dumps({})
payload = payload.encode("utf-8")
signature = hmac.new(key, payload, hashlib.sha256).hexdigest()

headers = {
    'X-CS-APIKEY': api_key,
    'X-CS-SIGN': signature,
    'X-CS-EXPIRES': str(expires),
    'exch-language': 'en_US',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Connection': 'keep-alive'
}
response = requests.request("POST", url, headers=headers, data=payload)
```

### Our Implementation Differences
1. **API Key Format**: Docs show `api_key = b'your api_key'` (bytes), we use strings
   - **Note**: `requests` accepts both, but `aiohttp` might handle differently
2. **Secret Key Format**: Docs show `secret_key = b'your secret_key'` (bytes)
   - We encode to bytes: `self.api_secret.encode('utf-8')`
3. **Payload Encoding**: Docs encode payload before signature: `payload.encode("utf-8")`
   - We encode inside signature function (should be equivalent)

---

## ❓ Questions for Dev

1. **API Key/Secret Format**
   - Should API key and secret be treated as bytes or strings?
   - Are there any encoding requirements (UTF-8, ASCII)?
   - Should we strip whitespace or handle any special characters?

2. **Signature Calculation**
   - Is our signature generation logic correct?
   - Are we missing any steps or transformations?
   - Should we test with the exact Coinstore Python SDK example?

3. **Payload Format**
   - Is the JSON payload format correct? (no spaces, sorted keys?)
   - Should `timestamp` be a number or string in the payload?
   - Are there any Coinstore-specific payload requirements?

4. **Request Headers**
   - Are all required headers present?
   - Is `exch-language` required or optional?
   - Should headers be in a specific order?

5. **API Configuration**
   - Are there API key permissions required (read, spot trading)?
   - Is IP whitelisting mandatory or optional?
   - Could account-level restrictions cause `signature-failed`?

6. **Testing**
   - Can we get a working Python example that successfully authenticates?
   - Should we test with `requests` library first to verify credentials?
   - Are there any Coinstore API test endpoints we can use?

---

## 🛠️ What We've Tried

1. ✅ Verified signature generation matches Coinstore docs exactly
2. ✅ Ensured payload JSON matches request body exactly
3. ✅ Confirmed timestamp in payload matches `X-CS-EXPIRES` header
4. ✅ Added detailed logging for signature calculation
5. ✅ Verified API key and secret are loaded correctly
6. ✅ Checked IP whitelisting configuration
7. ✅ Tested with both balance and order endpoints (both fail)

---

## 📁 Relevant Files

- `app/coinstore_connector.py` - Signature generation and API requests
- `app/coinstore_adapter.py` - ccxt-compatible adapter wrapper
- `app/cex_volume_bot.py` - Bot logic that calls exchange

---

## 🎯 Next Steps (Pending Dev Input)

1. Get confirmation on API key/secret format requirements
2. Test with Coinstore Python SDK example to verify credentials
3. Compare our signature calculation with working example
4. Verify API key permissions and IP whitelisting
5. Test with `requests` library to isolate aiohttp vs signature issue

---

## 📞 Contact

**Server:** Hetzner VPS (5.161.64.209)  
**Bot ID:** `da71f660-2a8a-42e9-a94f-6fde3e9789a3`  
**Exchange:** Coinstore  
**Pair:** SHARP/USDT  

**Logs Location:** `/opt/trading-bridge/app.log` on Hetzner server

---

**Created:** 2026-02-10  
**Status:** Awaiting dev assistance to resolve signature authentication issue
