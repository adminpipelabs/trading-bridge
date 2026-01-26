# Update Railway with ngrok URL

**Current Status:** Railway variable still shows `http://hummingbot-api:8000`

---

## 🔍 **Current Configuration**

**Debug endpoint shows:**
```json
{
  "HUMMINGBOT_API_URL": "http://hummingbot-api:8000"
}
```

**This is still the old value** - needs to be updated with ngrok URL.

---

## ✅ **Steps to Update**

### **Step 1: Get ngrok URL**

**If ngrok is running, check:**
```bash
curl http://localhost:4040/api/tunnels
```

**Or look at ngrok terminal** - you'll see:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

---

### **Step 2: Update Railway Variable**

1. **Railway Dashboard** → **Trading Bridge service**
2. **Variables tab**
3. **Find `HUMMINGBOT_API_URL`**
4. **Change from:** `http://hummingbot-api:8000`
5. **Change to:** `https://your-ngrok-url.io`
   - Use the HTTPS URL from ngrok
   - **No port** `:8000` - ngrok handles that!
6. **Click Save**

---

### **Step 3: Wait for Redeploy**

Railway will auto-redeploy (1-2 minutes)

**Check logs** - should see deployment starting

---

### **Step 4: Verify**

**After redeploy, check debug endpoint:**
```bash
curl https://trading-bridge-production.up.railway.app/debug/env
```

**Should show:**
```json
{
  "HUMMINGBOT_API_URL": "https://your-ngrok-url.io"
}
```

---

### **Step 5: Test Connection**

```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Should return:** `{"bots":[]}` ✅

**Then test bot creation:**
```bash
curl -X POST https://trading-bridge-production.up.railway.app/bots/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_bot",
    "account": "client_sharp",
    "connector": "bitmart",
    "pair": "SHARP/USDT",
    "strategy": "spread",
    "config": {"bid_spread": 0.001, "ask_spread": 0.001, "order_amount": 100}
  }'
```

---

## ⚠️ **Important**

- **Keep ngrok running** - Don't close the terminal
- **Use HTTPS URL** - Not HTTP
- **No port** - ngrok handles port forwarding

---

**Once you update the Railway variable with ngrok URL, let me know and I'll test it!** 🚀
