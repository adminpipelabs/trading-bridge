# Quick Fix - ngrok Tunnel

**Fastest solution to connect local Hummingbot API to Railway**

---

## ⚡ **5-Minute Setup**

### **Step 1: Install ngrok**

```bash
brew install ngrok
```

### **Step 2: Start Tunnel**

```bash
ngrok http 8000
```

**Keep this terminal open!**

### **Step 3: Copy URL**

You'll see:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8000
```

**Copy:** `https://abc123.ngrok.io` (your URL will be different)

### **Step 4: Update Railway**

**Trading Bridge → Variables:**
```
HUMMINGBOT_API_URL=https://abc123.ngrok.io
```

**Important:** No `:8000` port - ngrok handles that!

### **Step 5: Test**

```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Should return:** `{"bots":[]}` ✅

---

## ⚠️ **Important Notes**

- **Keep ngrok running** - Close terminal = connection breaks
- **URL changes** - Each restart gets new URL (unless paid plan)
- **For testing only** - Use Railway deployment for production

---

**That's it! Connection should work now.** 🎉
