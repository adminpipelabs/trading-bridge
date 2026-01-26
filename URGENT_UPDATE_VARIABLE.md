# ⚠️ URGENT: Update Railway Variable

**Current Status:** Still using `http://hummingbot-api:8000` (won't work!)

---

## 🔴 **The Problem**

**Logs show:**
```
Connection failed to http://hummingbot-api:8000
```

**This means Railway variable hasn't been updated with ngrok URL yet!**

---

## ✅ **Quick Fix - 3 Steps**

### **Step 1: Get ngrok URL**

**Check your ngrok terminal** - you should see:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8000
```

**OR check via command:**
```bash
curl http://localhost:4040/api/tunnels
```

**Copy the HTTPS URL** (looks like `https://xxxxx.ngrok.io`)

---

### **Step 2: Update Railway Variable**

1. **Go to Railway Dashboard**
2. **Trading Bridge service**
3. **Variables tab**
4. **Find `HUMMINGBOT_API_URL`**
5. **Change value to:** `https://your-ngrok-url.io`
   - **Use HTTPS** (not HTTP)
   - **No port** `:8000`
   - **Full URL** from ngrok
6. **Click Save**

---

### **Step 3: Wait for Redeploy**

Railway will auto-redeploy (1-2 minutes)

**After redeploy, connection should work!**

---

## 🎯 **Example**

**Before:**
```
HUMMINGBOT_API_URL=http://hummingbot-api:8000
```

**After:**
```
HUMMINGBOT_API_URL=https://abc123.ngrok.io
```

---

## ✅ **Verify It Worked**

**After redeploy, check:**
```bash
curl https://trading-bridge-production.up.railway.app/debug/env
```

**Should show:**
```json
{
  "HUMMINGBOT_API_URL": "https://your-ngrok-url.io"
}
```

**Then test:**
```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Should return:** `{"bots":[]}` ✅

---

## ⚠️ **Important**

- **Keep ngrok running** - Don't close the terminal
- **Use HTTPS URL** - Not HTTP
- **No port number** - ngrok handles that

---

**Update the Railway variable now and it will work!** 🚀
