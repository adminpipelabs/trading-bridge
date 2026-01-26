# Start ngrok Tunnel

**Quick setup to connect local Hummingbot API to Railway**

---

## 🚀 **Steps**

### **Step 1: Start ngrok**

**In a terminal, run:**
```bash
ngrok http 8000
```

**Keep this terminal open!** (Closing it stops the tunnel)

### **Step 2: Copy the URL**

You'll see output like:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### **Step 3: Update Railway**

**Trading Bridge → Variables:**
- Find `HUMMINGBOT_API_URL`
- Change to: `https://your-ngrok-url.io`
- **Important:** No `:8000` port - ngrok handles that!
- Save

### **Step 4: Wait for Redeploy**

Railway will auto-redeploy (1-2 minutes)

### **Step 5: Test**

```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Expected:** `{"bots":[]}` ✅

---

## ⚠️ **Important**

- **Keep ngrok running** - Don't close the terminal
- **URL changes** - Each restart gets new URL (unless paid plan)
- **For testing** - Use Railway deployment for production

---

**Ready to start ngrok? Run: `ngrok http 8000`** 🚀
