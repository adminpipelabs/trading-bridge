# Production Deployment Guide

**Trading Bridge + Hummingbot API Integration**

---

## 📋 **Prerequisites**

- ✅ Hummingbot API deployed to Railway
- ✅ PostgreSQL database running (for Hummingbot)
- ✅ Both services in same Railway project (for internal networking)

---

## 🔧 **Step 1: Deploy Hummingbot API**

### **1.1 Create Railway Service**

1. **Railway Dashboard** → Your Project
2. **New Service** → **Deploy from Docker Hub**
3. **Docker Image:** `hummingbot/hummingbot:latest` (or your custom image)
4. **Service Name:** `hummingbot-api` (note this name - you'll need it)

### **1.2 Configure Environment Variables**

**Required Variables:**
```bash
# Database
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Use Railway Postgres addon

# API Configuration
HUMMINGBOT_API_PORT=8000
HUMMINGBOT_API_USERNAME=admin
HUMMINGBOT_API_PASSWORD=<secure_password>

# Optional: API Key (alternative to username/password)
# HUMMINGBOT_API_KEY=<api_key>
```

### **1.3 Configure Port**

1. **Service Settings** → **Networking**
2. **Port:** `8000`
3. **Public:** `Off` (internal only)

### **1.4 Deploy and Verify**

1. **Deploy** the service
2. **Check Logs** - should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   INFO:     Application startup complete
   ```

---

## 🔧 **Step 2: Configure Trading Bridge**

### **2.1 Find Hummingbot API Service Name**

**In Railway Dashboard:**
1. **Your Project** → **Services List**
2. **Find Hummingbot API service**
3. **Note the service name** (e.g., `hummingbot-api`)

**Common Names:**
- `hummingbot-api` (most common)
- `hummingbot`
- Check service settings if unsure

### **2.2 Set Environment Variables**

**Go to Trading Bridge Service** → **Variables Tab**

**Add/Update:**
```bash
# Required: Hummingbot API Connection
HUMMINGBOT_API_URL=http://hummingbot-api:8000
# Replace 'hummingbot-api' with actual service name

# Required: Authentication (choose one)
HUMMINGBOT_API_USERNAME=admin
HUMMINGBOT_API_PASSWORD=<same_password_as_hummingbot>

# OR use API Key instead:
# HUMMINGBOT_API_KEY=<api_key>

# Optional: Environment
ENVIRONMENT=production
```

**Important:**
- Use **internal service name** (not public URL)
- Format: `http://[SERVICE_NAME]:8000`
- Both services must be in **same Railway project**

### **2.3 Verify Configuration**

**After setting variables, Railway will auto-redeploy.**

**Check Trading Bridge Logs:**
```
✅ Good:
HummingbotClient initialized: http://hummingbot-api:8000 (auth: BASIC)

❌ Bad:
HummingbotClient initialized: http://localhost:8000
```

**If you see `localhost`, the variable is not set correctly.**

---

## ✅ **Step 3: Verify Deployment**

### **3.1 Test Trading Bridge Health**

```bash
curl https://trading-bridge-production.up.railway.app/
```

**Expected:**
```json
{
  "service": "Trading Bridge",
  "version": "1.0.0",
  "status": "online"
}
```

### **3.2 Test Bot Endpoints**

**List Bots:**
```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Expected:**
```json
{
  "bots": []
}
```

**Create Bot:**
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

**Expected:** Bot creation response or error with details

---

## 🔍 **Troubleshooting**

### **Issue: "Connection failed to localhost:8000"**

**Problem:** `HUMMINGBOT_API_URL` not set or wrong

**Fix:**
1. Check Trading Bridge Variables
2. Verify `HUMMINGBOT_API_URL` is set
3. Use internal service name: `http://hummingbot-api:8000`
4. Ensure both services in same project

---

### **Issue: "All connection attempts failed"**

**Problem:** Can't reach Hummingbot API

**Check:**
1. **Hummingbot API running?** Check logs for "Uvicorn running"
2. **Service name correct?** Verify in Railway dashboard
3. **Same project?** Both services must be in same Railway project
4. **Port correct?** Should be `8000`

---

### **Issue: "Not authenticated"**

**Problem:** Wrong credentials

**Fix:**
1. Verify `HUMMINGBOT_API_USERNAME` matches Hummingbot API
2. Verify `HUMMINGBOT_API_PASSWORD` matches Hummingbot API
3. Or use `HUMMINGBOT_API_KEY` if configured

---

### **Issue: "Configuration Error" at startup**

**Problem:** Missing required environment variables

**Fix:**
1. Check Trading Bridge logs for specific error
2. Set missing variables
3. Redeploy

---

## 📊 **Production Checklist**

- [ ] Hummingbot API deployed and running
- [ ] PostgreSQL database connected to Hummingbot API
- [ ] Hummingbot API service name identified
- [ ] `HUMMINGBOT_API_URL` set in Trading Bridge
- [ ] `HUMMINGBOT_API_USERNAME` set in Trading Bridge
- [ ] `HUMMINGBOT_API_PASSWORD` set in Trading Bridge
- [ ] Both services in same Railway project
- [ ] Trading Bridge logs show correct URL (not localhost)
- [ ] `/bots` endpoint returns `{"bots":[]}`
- [ ] Bot creation test successful

---

## 🔐 **Security Notes**

1. **Use strong passwords** for `HUMMINGBOT_API_PASSWORD`
2. **Consider API keys** instead of username/password
3. **Keep services internal** (don't expose Hummingbot API publicly)
4. **Use Railway secrets** for sensitive values
5. **Rotate credentials** periodically

---

## 📚 **Additional Resources**

- **Hummingbot API Docs:** Check Hummingbot documentation
- **Railway Networking:** https://docs.railway.app/develop/networking
- **Service Discovery:** Railway services can reach each other via service name

---

## 🚀 **Next Steps**

After successful deployment:
1. Test bot creation via API
2. Test bot start/stop
3. Integrate with frontend UI
4. Monitor logs for errors
5. Set up alerts for failures

---

**Deployment complete!** ✅
