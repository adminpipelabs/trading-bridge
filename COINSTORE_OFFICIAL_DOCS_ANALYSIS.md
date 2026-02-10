# Coinstore Official Docs Analysis

**Source:** https://coinstore-openapi.github.io/en/

---

## ✅ **Our Implementation Matches Official Docs**

**Official Python Example:**
```python
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

**Our Implementation:** ✅ Matches exactly

---

## 🔍 **Critical Finding from Docs**

**IP Whitelisting:**
> "Each user can create 5 groups of API Keys, and each group of API Keys can bind 5 different IP addresses. **Once an API key binds an address, the API interface can only be called by using the API key from the bound IP address.**"

**This means:**
- If API key has IPs bound → **MUST use one of those IPs**
- If API key has NO IPs bound → Can use from any IP
- Hetzner IP `5.161.64.209` **MUST be in the bound IP list**

---

## 🎯 **The Real Issue**

**1401 Unauthorized = IP not whitelisted OR credentials wrong**

**Check on Coinstore Dashboard:**
1. API Key: `42b5c7c40bf625e7fcffd16a654b6ed0`
2. **IP Binding:** Does it have IPs bound?
   - If YES → Is `5.161.64.209` in the list?
   - If NO → Should work from any IP
3. **API Secret:** Does it match database?

---

## ✅ **What We Know**

- ✅ Code matches official docs exactly
- ✅ Signature algorithm correct
- ✅ Headers correct
- ✅ Payload correct
- ❌ Still 1401 → IP whitelist or secret issue

---

**The code is correct. The issue is Coinstore configuration (IP whitelist or secret).**
