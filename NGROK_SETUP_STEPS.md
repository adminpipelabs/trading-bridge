# ngrok Setup - Step by Step

**Follow these steps to connect local Hummingbot API to Railway**

---

## 🚀 **Step 1: Start ngrok**

**Open a new terminal and run:**
```bash
ngrok http 8000
```

**Keep this terminal open!** (Don't close it)

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
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL:** `https://abc123.ngrok.io`  
*(Your URL will be different)*

---

## ⚙️ **Step 3: Update Railway Variable**

1. **Go to Railway Dashboard**
2. **Trading Bridge service** → **Variables tab**
3. **Find `HUMMINGBOT_API_URL`**
4. **Change value to:** `https://your-ngrok-url.io`
   - **Important:** Use the HTTPS URL you copied
   - **No port** `:8000` - ngrok handles that!
5. **Click Save**

---

## ⏳ **Step 4: Wait for Redeploy**

Railway will auto-redeploy (1-2 minutes)

**You'll see:**
- Deployment starting
- New deployment in progress

---

## ✅ **Step 5: Test Connection**

**After redeploy, test:**
```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Expected result:**
```json
{"bots":[]}
```

**If you see this, it's working!** ✅

---

## 🎯 **Quick Test Bot Creation**

**Once connection works, test creating a bot:**
```bash
curl -X POST https://trading-bridge-production.up.railway.app/bots/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_bot",
    "account": "client_sharp",
    "connector": "bitmart",
    "pair": "SHARP/USDT",
    "strategy": "spread",
    "config": {
      "bid_spread": 0.001,
      "ask_spread": 0.001,
      "order_amount": 100
    }
  }'
```

---

## ⚠️ **Important Notes**

- **Keep ngrok running** - Don't close the terminal
- **URL changes** - Each restart gets new URL (unless paid plan)
- **For production** - Deploy Hummingbot to Railway instead

---

## 🔧 **If ngrok Stops**

**If you close ngrok or it stops:**
1. Restart: `ngrok http 8000`
2. Get new URL
3. Update Railway variable again

---

**Ready? Start ngrok now: `ngrok http 8000`** 🚀
