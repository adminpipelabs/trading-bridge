# Start ngrok - Quick Guide

**Action needed:** Start ngrok tunnel to expose local Hummingbot API

---

## 🚀 **Step 1: Start ngrok**

**Open a terminal and run:**
```bash
ngrok http 8000
```

**Keep this terminal open!** (Don't close it - ngrok needs to keep running)

---

## 📋 **Step 2: Copy the URL**

**You'll see output like:**
```
Session Status                online
Account                       Your Account
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000
```

**Copy the HTTPS URL:** `https://abc123.ngrok-free.app`

*(Your URL will be different - look for the "Forwarding" line)*

---

## ⚙️ **Step 3: Update Railway**

**Once you have the URL:**

1. **Railway Dashboard** → **Trading Bridge service**
2. **Variables tab**
3. **Find `HUMMINGBOT_API_URL`**
4. **Change from:** `http://hummingbot-api:8000`
5. **Change to:** `https://your-ngrok-url.ngrok-free.app`
   - Use HTTPS (not HTTP)
   - No port `:8000` - ngrok handles that
   - Full URL from ngrok
6. **Click Save**

---

## ⏳ **Step 4: Wait for Redeploy**

Railway will auto-redeploy (1-2 minutes)

---

## ✅ **Step 5: Test**

**After redeploy, test:**
```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Should return:** `{"bots":[]}` ✅

**Then test bot creation via UI!**

---

## ⚠️ **Important**

- **Keep ngrok running** - Don't close the terminal
- **Use HTTPS URL** - Not HTTP
- **No port number** - ngrok handles port forwarding
- **URL changes** - Each restart gets new URL (unless paid plan)

---

**Start ngrok now and share the URL when you have it!** 🚀
