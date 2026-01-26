# Solution Guide - Network Connection Issue

**Problem:** Hummingbot API is on your Mac, Trading Bridge is on Railway - they can't communicate

---

## 🎯 **Three Solutions**

| Solution | Time | Best For | Pros | Cons |
|----------|------|----------|------|------|
| **1. ngrok** | 5 min | Quick testing | Fast setup | URL changes on restart |
| **2. Deploy to Railway** | 30 min | Production | Permanent, reliable | Requires deployment |
| **3. Tailscale** | 10 min | If already using | Secure VPN | Need Tailscale working |

---

## 🚀 **Solution 1: ngrok Tunnel (Quickest)**

### **Step 1: Install ngrok**

```bash
brew install ngrok
```

### **Step 2: Start Tunnel**

```bash
# Expose Hummingbot API (running on localhost:8000)
ngrok http 8000
```

### **Step 3: Copy URL**

You'll see something like:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### **Step 4: Update Railway Variable**

**Trading Bridge → Variables:**
```
HUMMINGBOT_API_URL=https://abc123.ngrok.io
```

**Note:** Remove the port `:8000` - ngrok handles that.

### **Step 5: Test**

```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Downside:** URL changes each time you restart ngrok (unless paid plan)

---

## 🏗️ **Solution 2: Deploy Hummingbot to Railway (Recommended)**

### **Step 1: Create Railway Service**

1. **Railway Dashboard** → Your Project
2. **New Service** → **Deploy from Docker Hub**
3. **Docker Image:** `hummingbot/hummingbot-api:latest`
   - Or your custom image if different
4. **Service Name:** `hummingbot-api` (note this name)

### **Step 2: Configure Environment**

**Set Variables:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Use Railway Postgres addon
HUMMINGBOT_API_PORT=8000
HUMMINGBOT_API_USERNAME=admin
HUMMINGBOT_API_PASSWORD=<your_password>
```

### **Step 3: Configure Port**

1. **Service Settings** → **Networking**
2. **Port:** `8000`
3. **Public:** `Off` (internal only - for security)

### **Step 4: Update Trading Bridge**

**Trading Bridge → Variables:**
```
HUMMINGBOT_API_URL=http://hummingbot-api:8000
```

**Note:** Use internal service name (no `.railway.internal` needed in same project)

### **Step 5: Deploy and Test**

1. **Deploy Hummingbot API service**
2. **Wait for it to start** (check logs for "Uvicorn running")
3. **Trading Bridge will auto-redeploy**
4. **Test:**
   ```bash
   curl https://trading-bridge-production.up.railway.app/bots
   ```

**Benefits:**
- ✅ Permanent solution
- ✅ No tunnels needed
- ✅ Same network = fast
- ✅ Production-ready

---

## 🔐 **Solution 3: Fix Tailscale**

### **Step 1: Reinstall Tailscale**

```bash
# Uninstall
brew uninstall tailscale

# Reinstall
brew install tailscale

# Or download from website
open https://tailscale.com/download/mac
```

### **Step 2: Start Tailscale**

```bash
sudo tailscale up
```

### **Step 3: Get Your Tailscale IP**

```bash
tailscale ip -4
```

**Example output:** `100.64.0.5`

### **Step 4: Update Railway Variable**

**Trading Bridge → Variables:**
```
HUMMINGBOT_API_URL=http://100.64.0.5:8000
```

**Replace `100.64.0.5` with your actual Tailscale IP**

### **Step 5: Test**

```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Note:** Tailscale must be running on your Mac for this to work

---

## 🎯 **Recommendation**

### **For Testing:**
→ Use **ngrok** (Solution 1) - fastest to set up

### **For Production:**
→ Deploy **Hummingbot to Railway** (Solution 2) - permanent, reliable

### **If Already Using Tailscale:**
→ Fix **Tailscale** (Solution 3) - secure VPN solution

---

## 📋 **Quick Decision Guide**

**Choose ngrok if:**
- ✅ You want to test quickly
- ✅ Temporary setup is fine
- ✅ Don't mind URL changing

**Choose Railway deployment if:**
- ✅ You want production-ready solution
- ✅ Need permanent connection
- ✅ Want everything in one place

**Choose Tailscale if:**
- ✅ You already use Tailscale
- ✅ Want secure VPN connection
- ✅ Don't mind keeping Tailscale running

---

## ✅ **After Setup**

**Test the connection:**
```bash
# Test bot list
curl https://trading-bridge-production.up.railway.app/bots

# Test bot creation
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

**Which solution would you like to implement?** 🚀
