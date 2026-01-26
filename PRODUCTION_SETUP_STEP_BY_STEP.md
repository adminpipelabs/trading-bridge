# Production Setup - Step by Step Guide

**Approach:** Production-ready deployment (Hummingbot on Railway)  
**Pace:** Slow and methodical - verify each step before proceeding

---

## 🎯 **Goal**

Deploy Hummingbot to Railway so Trading Bridge can connect to it reliably without VPN.

---

## 📋 **Step-by-Step Plan**

### **Phase 1: Prepare Hummingbot for Railway** (15 min)
### **Phase 2: Deploy Hummingbot to Railway** (15 min)
### **Phase 3: Configure Trading Bridge** (5 min)
### **Phase 4: Test Integration** (10 min)

**Total Time:** ~45 minutes

---

## ✅ **PHASE 1: Prepare Hummingbot for Railway**

### **Step 1.1: Check Current Hummingbot Setup**

**Run:**
```bash
cd /Users/mikaelo/hummingbot-api
ls -la
```

**What to check:**
- [ ] `docker-compose.yml` exists
- [ ] `.env` file exists (or check what env vars are needed)
- [ ] Understand current configuration

**Expected:** See docker-compose.yml and related files

**✅ Verify before proceeding:** List files and confirm structure

---

### **Step 1.2: Review Docker Compose File**

**Run:**
```bash
cat docker-compose.yml
```

**What to look for:**
- [ ] Hummingbot API service definition
- [ ] Environment variables
- [ ] Port mappings (should expose port 8000)
- [ ] Database connection
- [ ] Volume mounts

**✅ Verify before proceeding:** Understand the current setup

---

### **Step 1.3: Check Environment Variables**

**Run:**
```bash
cat .env 2>/dev/null || echo "No .env file found"
```

**OR check inside container:**
```bash
docker exec hummingbot-api env | grep -i "api\|auth\|user\|pass\|database" | sort
```

**What to note:**
- [ ] API username (we know it's `admin`)
- [ ] API password (we know it's `admin`)
- [ ] Database URL
- [ ] Any other required variables

**✅ Verify before proceeding:** Have list of required environment variables

---

### **Step 1.4: Test Current Setup**

**Run:**
```bash
curl -u admin:admin http://localhost:8000/bot-orchestration/status
```

**Expected:**
```json
{"status":"success","data":{}}
```

**✅ Verify before proceeding:** Hummingbot API works locally

---

## ✅ **PHASE 2: Deploy Hummingbot to Railway**

### **Step 2.1: Create Railway Service**

**Action:**
1. Go to Railway Dashboard
2. Select your project (or create new)
3. Click **+ New** → **Service**
4. Choose **Deploy from GitHub** (if repo exists) OR **Empty Service**

**✅ Verify before proceeding:** Service created in Railway

---

### **Step 2.2: Configure Service**

**If deploying from Docker:**

**Option A: Use Dockerfile**
1. Create `Dockerfile` in hummingbot-api directory
2. Railway will auto-detect and use it

**Option B: Use Docker Image**
1. In Railway service settings
2. Set **Source** to **Docker Hub**
3. Image: `hummingbot/hummingbot-api:latest`

**✅ Verify before proceeding:** Service configured with Docker image

---

### **Step 2.3: Set Environment Variables**

**In Railway service → Variables tab, add:**

```bash
# API Authentication
USERNAME=admin
PASSWORD=admin
CONFIG_PASSWORD=admin

# Database (if needed)
DATABASE_URL=postgresql+asyncpg://hbot:hummingbot-api@postgres:5432/hummingbot_api

# Broker (if needed)
BROKER_USERNAME=admin
BROKER_PASSWORD=password

# Gateway (if needed)
GATEWAY_PASSPHRASE=admin

# Paths
BOTS_PATH=/app/bots
```

**Note:** Adjust based on what you found in Step 1.3

**✅ Verify before proceeding:** All environment variables set

---

### **Step 2.4: Configure Port**

**In Railway service → Settings:**

1. Go to **Networking** tab
2. Add port mapping:
   - **Port:** `8000`
   - **Protocol:** `HTTP`

**OR Railway will auto-detect port 8000**

**✅ Verify before proceeding:** Port 8000 exposed

---

### **Step 2.5: Deploy**

**Action:**
1. Railway will auto-deploy when you save changes
2. OR click **Deploy** button
3. Wait for deployment to complete

**Monitor:**
- Go to **Deployments** tab
- Watch logs for errors
- Wait for "Deployment successful"

**✅ Verify before proceeding:** Deployment successful, no errors in logs

---

### **Step 2.6: Get Service URL**

**After deployment:**

1. Go to **Settings** → **Networking**
2. Find **Public URL** or **Internal URL**
3. Copy the URL

**For internal communication (same Railway project):**
- Use format: `http://hummingbot-api:8000`
- Or check Railway's internal DNS name

**For external access:**
- Use the public URL Railway provides

**✅ Verify before proceeding:** Have service URL

---

### **Step 2.7: Test Hummingbot on Railway**

**Run:**
```bash
curl -u admin:admin <railway-hummingbot-url>/bot-orchestration/status
```

**Expected:**
```json
{"status":"success","data":{}}
```

**✅ Verify before proceeding:** Hummingbot API responds on Railway

---

## ✅ **PHASE 3: Configure Trading Bridge**

### **Step 3.1: Get Hummingbot Service URL**

**From Step 2.6, you should have:**
- Internal URL: `http://hummingbot-api:8000` (if same project)
- OR Public URL: `https://hummingbot-api-production.up.railway.app`

**✅ Verify before proceeding:** Have Hummingbot URL

---

### **Step 3.2: Set Trading Bridge Environment Variables**

**Go to Railway Dashboard:**
1. Select **Trading Bridge** service
2. Go to **Variables** tab
3. Add/update these variables:

```bash
HUMMINGBOT_API_URL=http://hummingbot-api:8000
HUMMINGBOT_API_USERNAME=admin
HUMMINGBOT_API_PASSWORD=admin
```

**Note:** 
- Use internal URL if both services in same Railway project
- Use public URL if different projects

**✅ Verify before proceeding:** Variables set correctly

---

### **Step 3.3: Redeploy Trading Bridge**

**Action:**
1. Railway will auto-redeploy when variables are added
2. OR manually trigger redeploy
3. Wait for deployment to complete

**Monitor:**
- Check **Deployments** tab
- Watch logs for:
  - "HummingbotClient initialized: ..."
  - Any connection errors

**✅ Verify before proceeding:** Trading Bridge deployed successfully

---

## ✅ **PHASE 4: Test Integration**

### **Step 4.1: Test Trading Bridge Root**

**Run:**
```bash
curl https://trading-bridge-production.up.railway.app/
```

**Expected:**
```json
{"service":"Trading Bridge","version":"1.0.0","status":"online"}
```

**✅ Verify before proceeding:** Trading Bridge is online

---

### **Step 4.2: Test Get Bots Endpoint**

**Run:**
```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Expected:**
```json
{
  "bots": [
    // List of bots from Hummingbot, or empty array if none
  ]
}
```

**✅ Verify before proceeding:** Endpoint responds (even if empty)

---

### **Step 4.3: Test Create Bot**

**Run:**
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/bots/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_bot_production",
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

**Expected:**
```json
{
  "id": "test_bot_production",
  "name": "test_bot_production",
  "status": "running",
  "strategy": "spread",
  "connector": "bitmart",
  "pair": "SHARP/USDT",
  ...
}
```

**✅ Verify before proceeding:** Bot created successfully

---

### **Step 4.4: Verify Bot in Hummingbot**

**Check Railway logs:**
1. Go to Hummingbot service → Logs
2. Look for bot startup messages
3. Verify bot is running

**OR check Hummingbot API:**
```bash
curl -u admin:admin <hummingbot-url>/bot-orchestration/status
```

**Expected:** Bot appears in status response

**✅ Verify before proceeding:** Bot exists in Hummingbot

---

### **Step 4.5: Test Start/Stop**

**Stop bot:**
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/bots/test_bot_production/stop"
```

**Expected:** Bot status changes to "stopped"

**Start bot:**
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/bots/test_bot_production/start"
```

**Expected:** Bot status changes to "running"

**✅ Verify before proceeding:** Start/stop works correctly

---

## 📝 **Checklist**

### **Phase 1: Preparation**
- [ ] Checked current Hummingbot setup
- [ ] Reviewed docker-compose.yml
- [ ] Listed environment variables
- [ ] Tested local Hummingbot API

### **Phase 2: Deployment**
- [ ] Created Railway service
- [ ] Configured Docker/image
- [ ] Set environment variables
- [ ] Configured port 8000
- [ ] Deployed successfully
- [ ] Got service URL
- [ ] Tested Hummingbot on Railway

### **Phase 3: Configuration**
- [ ] Got Hummingbot URL
- [ ] Set Trading Bridge variables
- [ ] Redeployed Trading Bridge
- [ ] Verified deployment

### **Phase 4: Testing**
- [ ] Tested Trading Bridge root
- [ ] Tested get bots endpoint
- [ ] Tested create bot
- [ ] Verified bot in Hummingbot
- [ ] Tested start/stop

---

## 🚨 **Troubleshooting**

### **Issue: Hummingbot won't deploy**

**Check:**
- Docker image name correct?
- Environment variables set?
- Port 8000 exposed?
- Check Railway logs for errors

**Solution:** Review logs, fix configuration, redeploy

---

### **Issue: Trading Bridge can't connect**

**Check:**
- Hummingbot URL correct?
- Both services in same Railway project?
- Environment variables set?
- Check Trading Bridge logs

**Solution:** Verify URL, check logs, test connection

---

### **Issue: Bot creation fails**

**Check:**
- Hummingbot API accessible?
- Credentials correct?
- Script generation working?
- Check Railway logs

**Solution:** Test Hummingbot API directly, check logs

---

## 📊 **Progress Tracking**

**Current Phase:** [Fill in]
**Current Step:** [Fill in]
**Status:** [Fill in]
**Blockers:** [Fill in]

---

## 💡 **Notes**

- Take your time with each step
- Verify before proceeding
- Check logs if something fails
- Don't rush - production setup needs to be correct

---

**Ready to start Phase 1?** 🚀
