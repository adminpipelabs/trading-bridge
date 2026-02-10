# Dev's Test Script - Direct Signature Test

## 🎯 Purpose

Test if signature works with `requests` library (not `aiohttp`). This will tell us if:
- ✅ Signature works → Bug is in `aiohttp` request handling
- ❌ Signature fails → Bug is in signature generation OR account settings

---

## 📝 Test Script (Dev's Suggestion)

**Run this directly in Python shell on Hetzner server:**

```python
import hashlib, hmac, json, math, time, requests

# Get credentials from database (need to decrypt)
# For now, using hardcoded values from dev's example:
secret = b"e704b1ffa89e2ffabb85cfd589e99685"  # Replace with actual secret
api_key = "42b5c7c40bf625e7fcffd16a654b6ed0"  # Replace with actual key

expires = int(time.time() * 1000)
key = hmac.new(secret, str(math.floor(expires/30000)).encode(), hashlib.sha256).hexdigest()

# Test 1: Balance check (simplest)
payload = json.dumps({})
sig = hmac.new(key.encode(), payload.encode(), hashlib.sha256).hexdigest()

r = requests.post("https://api.coinstore.com/api/spot/accountList",
    data=payload,
    headers={"X-CS-APIKEY": api_key, "X-CS-SIGN": sig,
             "X-CS-EXPIRES": str(expires), "Content-Type": "application/json",
             "exch-language": "en_US"})
print("Balance check:", r.status_code, r.text[:200])

# Test 2: Order placement (if balance works)
if r.status_code == 200:
    expires = int(time.time() * 1000)
    key = hmac.new(secret, str(math.floor(expires/30000)).encode(), hashlib.sha256).hexdigest()
    
    params = {"symbol":"SHARPUSDT","side":"BUY","ordType":"MARKET",
              "ordAmt":"1","timestamp": expires}
    payload = json.dumps(params, separators=(',',':'))
    sig = hmac.new(key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    
    r2 = requests.post("https://api.coinstore.com/api/trade/order/place",
        data=payload,
        headers={"X-CS-APIKEY": api_key, "X-CS-SIGN": sig,
                 "X-CS-EXPIRES": str(expires), "Content-Type": "application/json",
                 "exch-language": "en_US"})
    print("Order placement:", r2.status_code, r2.text[:200])
    
    # If 401, test with default JSON separators
    if r2.status_code == 401:
        payload_default = json.dumps(params)  # Default separators
        sig_default = hmac.new(key.encode(), payload_default.encode(), hashlib.sha256).hexdigest()
        r3 = requests.post("https://api.coinstore.com/api/trade/order/place",
            data=payload_default,
            headers={"X-CS-APIKEY": api_key, "X-CS-SIGN": sig_default,
                     "X-CS-EXPIRES": str(expires), "Content-Type": "application/json",
                     "exch-language": "en_US"})
        print("Order (default separators):", r3.status_code, r3.text[:200])
```

---

## 🔍 What to Check

### 1. Get Actual Credentials
**On Hetzner server:**
```bash
cd /opt/trading-bridge
source venv/bin/activate
python3 -c "
from app.security import decrypt_credential
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
load_dotenv('.env')

engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    row = conn.execute(text(\"SELECT api_key_encrypted, api_secret_encrypted FROM exchange_credentials WHERE exchange='coinstore' LIMIT 1\")).fetchone()
    if row:
        print('API Key:', decrypt_credential(row[0]))
        print('Secret:', decrypt_credential(row[1])[:20] + '...')
"
```

### 2. Verify Server IP
```bash
curl -4 ifconfig.me
# Should be: 5.161.64.209
```

### 3. Run Test Script
Use credentials from step 1 in the test script above.

---

## 📊 Expected Results

### Scenario A: Balance Check Returns 200
**Meaning:** Signature works with `requests` library  
**Conclusion:** Bug is in `aiohttp` request handling  
**Fix:** Use `requests` library or fix `aiohttp` body encoding

### Scenario B: Balance Check Returns 401
**Meaning:** Signature fails even with `requests`  
**Possible causes:**
1. IP whitelist issue (`5.161.64.209` not whitelisted)
2. API key permissions (Spot Trading not enabled)
3. Signature generation bug (less likely if code matches docs)

### Scenario C: Balance Works, Order Fails with Compact JSON
**Meaning:** Signature works but JSON separators matter  
**Fix:** Try default `json.dumps(params)` without `separators=(',', ':')`

### Scenario D: Order Works with Default Separators
**Meaning:** Coinstore expects default JSON formatting  
**Fix:** Remove `separators=(',', ':')` from `json.dumps()`

---

## 🎯 Most Likely Outcomes

**90% chance:** Balance check returns 401 → Account settings issue (IP whitelist or permissions)

**10% chance:** Balance works, order fails → JSON separators issue or aiohttp bug

---

## 📝 Next Steps After Test

1. **If 401 on balance:** Check Coinstore dashboard → IP whitelist → Permissions
2. **If 200 on balance, 401 on order:** Test default JSON separators
3. **If 200 on both:** Signature works → Bug is in `aiohttp` → Fix connector

---

**Created:** 2026-02-10  
**Purpose:** Concrete test to identify root cause
