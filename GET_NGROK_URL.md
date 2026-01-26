# Get ngrok URL - Quick Steps

**Follow these steps to get your ngrok URL**

---

## 🚀 **Step 1: Install ngrok (if needed)**

```bash
brew install ngrok
```

---

## 🚀 **Step 2: Start ngrok**

**In a terminal, run:**
```bash
ngrok http 8000
```

**Keep this terminal open!** (Don't close it)

---

## 📋 **Step 3: Copy the URL**

**You'll see output like:**
```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8000
```

**Copy the HTTPS URL:** `https://abc123.ngrok-free.app`

*(Your URL will be different)*

---

## ⚙️ **Step 4: Update Railway**

1. **Railway Dashboard** → **Trading Bridge service**
2. **Variables tab**
3. **Find `HUMMINGBOT_API_URL`**
4. **Change to:** `https://abc123.ngrok-free.app` (your URL)
   - **Use HTTPS** (not HTTP)
   - **No port** `:8000` - ngrok handles that
5. **Click Save**

---

## ⏳ **Step 5: Wait for Redeploy**

Railway will auto-redeploy (1-2 minutes)

---

## ✅ **Step 6: Test**

**After redeploy, test bot creation:**
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/bots/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Bot",
    "account": "client_sharp",
    "connector": "bitmart",
    "pair": "SHARP/USDT",
    "strategy": "spread",
    "config": {
      "spread_pct": 0.3,
      "amount": 1600
    }
  }'
```

**Expected:** Bot creation response ✅

---

## ⚠️ **Important**

- **Keep ngrok running** - Don't close the terminal
- **Use HTTPS URL** - Not HTTP
- **No port number** - ngrok handles port forwarding

---

**Once you have the ngrok URL, share it and I'll help update Railway!** 🚀
