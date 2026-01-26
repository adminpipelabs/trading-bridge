# Dev Help Request - Authentication Issue

**Date:** 2026-01-26  
**Issue:** 401 Authentication Error - Need Dev Advice

---

## ✅ **What's Working**

- ✅ ngrok tunnel: `https://unpolymerized-singlemindedly-theda.ngrok-free.dev`
- ✅ Direct authentication test works: `curl -u admin:admin https://ngrok-url/status` ✅
- ✅ Credentials verified in container: Username=`admin`, Password=`admin`
- ✅ Connection established successfully
- ✅ `/bots` endpoint returns `{"bots":[]}` ✅
- ✅ Code complete with debug logging

---

## ❌ **Current Issue**

**Bot creation fails with:**
```
HTTP error 401: {"detail":"Incorrect username or password"}
```

**Even though:**
- Direct ngrok test works with `admin:admin` ✅
- Railway variables show password exists (`has_password: true`) ✅
- Username is `admin` ✅

---

## 🔍 **What We've Tried**

1. ✅ Verified credentials in Hummingbot API container
2. ✅ Tested direct authentication through ngrok (works!)
3. ✅ Updated Railway variables with `admin:admin`
4. ✅ Added debug logging to see what password is being read
5. ✅ Railway redeployed multiple times
6. ❌ Still getting 401 error

---

## 🤔 **Questions for Dev**

### **1. Authentication Format**

**Is there a specific format Hummingbot API expects?**
- Basic auth: `admin:admin` ✅ (works directly)
- But Railway → Hummingbot fails ❌
- Is there a different auth method needed?

### **2. Password Variable**

**Railway shows:**
- `HUMMINGBOT_API_USERNAME=admin` ✅
- `HUMMINGBOT_API_PASSWORD` exists (`has_password: true`) ✅
- But authentication still fails

**Questions:**
- Could password have hidden characters/spaces?
- Is Railway reading it correctly?
- Should we use a different variable name?

### **3. httpx Authentication**

**Current code:**
```python
self.auth = (self.username, self.password) if self.password else None
# Then in request:
request_kwargs["auth"] = self.auth
```

**Questions:**
- Is this the correct format for httpx basic auth?
- Should we use `httpx.BasicAuth()` instead?
- Is there an encoding issue?

### **4. Railway Environment Variables**

**We noticed:**
- URL variable had leading space: ` HUMMINGBOT_API_URL`
- Code handles this with: `os.getenv(" HUMMINGBOT_API_URL", "")`

**Questions:**
- Could password also have leading/trailing spaces?
- Should we trim password value?
- Is there a Railway quirk we're missing?

---

## 🔧 **Code Location**

**File:** `app/hummingbot_client.py`

**Current implementation:**
```python
self.username = os.getenv("HUMMINGBOT_API_USERNAME", "") or os.getenv(" HUMMINGBOT_API_USERNAME", "") or "hummingbot"
self.password = os.getenv("HUMMINGBOT_API_PASSWORD", "") or os.getenv(" HUMMINGBOT_API_PASSWORD", "")
# ...
self.auth = (self.username, self.password) if self.password else None
```

**In request:**
```python
if self.auth:
    request_kwargs["auth"] = self.auth
```

---

## 📋 **Debug Information**

**Debug endpoint shows:**
```json
{
  "HUMMINGBOT_API_URL": "https://unpolymerized-singlemindedly-theda.ngrok-free.dev",
  "HUMMINGBOT_API_USERNAME": "admin",
  "has_password": true,
  "all_env_keys": ["HUMMINGBOT_API_PASSWORD", " HUMMINGBOT_API_URL", "HUMMINGBOT_API_USERNAME"]
}
```

**Direct test works:**
```bash
curl -u admin:admin https://unpolymerized-singlemindedly-theda.ngrok-free.dev/bot-orchestration/status
# Returns: {"status":"success","data":{}}
```

**But Railway request fails:**
```bash
curl -X POST https://trading-bridge-production.up.railway.app/bots/create ...
# Returns: HTTP error 401: {"detail":"Incorrect username or password"}
```

---

## 🎯 **What We Need**

**Dev's advice on:**
1. **Why direct test works but Railway fails?**
2. **Is httpx auth format correct?**
3. **Should we trim password value?**
4. **Any Railway-specific authentication quirks?**
5. **Alternative authentication methods?**

---

## 💡 **Possible Solutions to Try**

1. **Use httpx.BasicAuth() explicitly:**
   ```python
   from httpx import BasicAuth
   self.auth = BasicAuth(self.username, self.password)
   ```

2. **Trim password value:**
   ```python
   self.password = (os.getenv("HUMMINGBOT_API_PASSWORD", "") or os.getenv(" HUMMINGBOT_API_PASSWORD", "")).strip()
   ```

3. **Add more debug logging:**
   ```python
   logger.info(f"Auth tuple: ({self.username}, '{self.password}')")
   ```

4. **Test password value directly:**
   - Log actual password value (masked)
   - Check for hidden characters

---

## 📁 **Files**

- `app/hummingbot_client.py` - Authentication code
- `app/bot_routes.py` - Bot creation endpoint
- Debug endpoint: `/debug/env`

---

## 🚀 **Status**

**Everything else works:**
- ✅ Network connection
- ✅ ngrok tunnel
- ✅ Code implementation
- ✅ Frontend UI
- ⚠️ Authentication failing

**Need dev's expertise to resolve authentication issue!** 🙏

---

**Thanks for your help!** 🙏
