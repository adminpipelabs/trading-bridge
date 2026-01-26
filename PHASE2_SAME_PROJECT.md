# Phase 2: Deploy Hummingbot to Railway - Same Project

**Using:** Existing Railway project (where Trading Bridge is deployed)  
**Benefit:** Can use internal service URLs for communication

---

## ✅ **STEP 2.1: Add Service to Existing Project**

### **Action:**

1. **Go to Railway Dashboard**
   - Open: https://railway.app/dashboard
   - Sign in

2. **Select Your Project**
   - Click on the project that contains **Trading Bridge**
   - You should see Trading Bridge service listed

3. **Add New Service**
   - Click **+ New** button (in the project)
   - Select **Empty Service**
   - Name it: `hummingbot-api` (optional, can rename later)

**✅ Verify:** New service appears in same project as Trading Bridge

**Status:** [ ] Complete - Service added to project

---

## ✅ **STEP 2.2: Configure Docker Image**

### **Action:**

1. **Click on the new service** (hummingbot-api)

2. **Go to Settings Tab**

3. **Find "Source" section**

4. **Set to Docker Hub:**
   - Click **Connect** or **Configure**
   - Select **Docker Hub**
   - Image: `hummingbot/hummingbot-api:latest`

**OR if Railway has "Deploy" option:**
- Go to **Deploy** tab
- Select **Docker Hub**
- Enter: `hummingbot/hummingbot-api:latest`

**✅ Verify:** Service configured with Docker image

**Status:** [ ] Complete - Docker image configured

---

## ✅ **STEP 2.3: Add Postgres Database**

### **Action:**

1. **In the SAME Railway project**

2. **Click + New** → **Database** → **Add Postgres**

3. **Wait for Postgres to deploy** (takes 1-2 minutes)

4. **Get Connection String:**
   - Click on **Postgres** service
   - Go to **Variables** tab
   - Find `DATABASE_URL` or `POSTGRES_URL`
   - Copy the connection string

**Example Railway Postgres URL:**
```
postgresql://postgres:password@containers-us-west-xxx.railway.app:5432/railway
```

**We need to convert this to asyncpg format:**
```
postgresql+asyncpg://postgres:password@containers-us-west-xxx.railway.app:5432/railway
```

**Note:** Just add `+asyncpg` after `postgresql`

**✅ Verify:** Postgres deployed, connection string copied

**Status:** [ ] Complete - Postgres added

---

## ✅ **STEP 2.4: Configure Port**

### **Action:**

1. **Go to hummingbot-api service**

2. **Settings** → **Networking** tab

3. **Add Port:**
   - Port: `8000`
   - Protocol: `HTTP`

**OR Railway may auto-detect port 8000 from Dockerfile**

**✅ Verify:** Port 8000 configured

**Status:** [ ] Complete - Port configured

---

## ✅ **STEP 2.5: Set Environment Variables**

### **Action:**

1. **Go to hummingbot-api service**

2. **Variables** tab

3. **Add these variables:**

```bash
# API Authentication
USERNAME=admin
PASSWORD=admin
CONFIG_PASSWORD=admin

# Database (use Railway Postgres - add +asyncpg)
DATABASE_URL=postgresql+asyncpg://postgres:password@containers-us-west-xxx.railway.app:5432/railway
# Replace with your actual Postgres URL from Step 2.3, add +asyncpg

# Broker (optional - can use localhost or skip)
BROKER_HOST=localhost
BROKER_USERNAME=admin
BROKER_PASSWORD=password

# Gateway (optional)
GATEWAY_PASSPHRASE=admin

# Paths
BOTS_PATH=/app/bots
```

**Important Steps:**
1. Copy `DATABASE_URL` from Postgres service Variables tab
2. Change `postgresql://` to `postgresql+asyncpg://`
3. Paste into hummingbot-api Variables

**✅ Verify:** All variables added, DATABASE_URL has +asyncpg

**Status:** [ ] Complete - Variables set

---

## ✅ **STEP 2.6: Deploy**

### **Action:**

1. **Railway will auto-deploy** when you add variables

2. **Monitor Deployment:**
   - Go to **Deployments** tab
   - Watch for "Deployment successful"
   - Check **Logs** tab for any errors

**Look for in logs:**
- "Application startup complete"
- "Uvicorn running on http://0.0.0.0:8000"
- Any error messages

**✅ Verify:** Deployment successful, no errors

**Status:** [ ] Complete - Deployed successfully

---

## ✅ **STEP 2.7: Get Service URL**

### **Action:**

1. **After deployment completes**

2. **Go to hummingbot-api service**

3. **Settings** → **Networking**

4. **Find Internal URL:**
   - Railway provides internal DNS name
   - Format: `http://hummingbot-api:8000` (if service named "hummingbot-api")
   - OR check **Variables** tab for `RAILWAY_SERVICE_NAME`

**For Trading Bridge (same project):**
- Use: `http://hummingbot-api:8000`
- OR: `http://<service-name>:8000`

**For external testing:**
- Use Public URL if available

**✅ Verify:** Have internal service URL

**Status:** [ ] Complete - URL obtained

---

## ✅ **STEP 2.8: Test Hummingbot on Railway**

### **Action:**

**Option A: Test with Public URL (if available)**
```bash
curl -u admin:admin https://hummingbot-api-production.up.railway.app/bot-orchestration/status
```

**Option B: Test from Railway logs**
- Check logs for startup messages
- Look for "Application startup complete"

**Expected Response:**
```json
{"status":"success","data":{}}
```

**✅ Verify:** API responds correctly

**Status:** [ ] Complete - API tested

---

## 📋 **Phase 2 Checklist**

- [ ] Step 2.1: Service added to Trading Bridge project
- [ ] Step 2.2: Docker image configured
- [ ] Step 2.3: Postgres added
- [ ] Step 2.4: Port configured
- [ ] Step 2.5: Environment variables set (with +asyncpg)
- [ ] Step 2.6: Deployed successfully
- [ ] Step 2.7: Internal service URL obtained
- [ ] Step 2.8: API tested

---

## 🎯 **Key Points**

1. **Same Project:** Both services in same Railway project
2. **Internal URLs:** Can use `http://hummingbot-api:8000` for communication
3. **Postgres:** Use Railway Postgres addon (easier than deploying)
4. **Database URL:** Must have `+asyncpg` for Hummingbot

---

**Ready to start Step 2.1?** 🚀
