# Find & Fix Service Name - Super Simple

**Current Problem:** Using `localhost:8000` (wrong)  
**Need:** Railway internal service name

---

## 🎯 **Method 1: Check Railway Dashboard (Easiest)**

1. **Go to Railway Dashboard** → Your Project
2. **Look at services** (left sidebar)
3. **Find "Hummingbot API" or similar**
4. **The service name is usually:**
   - `hummingbot-api` ← **Most likely**
   - `hummingbot`
   - Or check the service URL/settings

---

## 🔧 **Method 2: Try Common Names**

**Just try these in order:**

### **Try 1: `hummingbot-api`**
1. Trading Bridge → Variables
2. Set `HUMMINGBOT_API_URL=http://hummingbot-api:8000`
3. Wait 2 minutes
4. Check logs - if you see the correct URL (not localhost), it worked!

### **Try 2: `hummingbot`**
If Try 1 didn't work:
1. Set `HUMMINGBOT_API_URL=http://hummingbot:8000`
2. Wait 2 minutes
3. Check logs

---

## ✅ **After You Set It**

**Check Trading Bridge logs:**
- ✅ **Good:** `HummingbotClient initialized: http://hummingbot-api:8000`
- ❌ **Bad:** `HummingbotClient initialized: http://localhost:8000`

**Then test:**
```bash
curl https://trading-bridge-production.up.railway.app/bots
```

---

## 🚀 **Quick Action**

**Most likely fix:**
1. Trading Bridge → Variables
2. `HUMMINGBOT_API_URL` → Change to: `http://hummingbot-api:8000`
3. Save
4. Wait 2 minutes
5. Done!

**If that doesn't work, try `http://hummingbot:8000`**

---

**That's it! Just update the variable and wait.** 🎉
