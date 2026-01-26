# Phase 2: Deploy Hummingbot to Railway - Step by Step

**Current Step:** 2.1 - Create Railway Service

---

## ✅ **STEP 2.1: Create Railway Service**

### **Action:**

1. **Go to Railway Dashboard**
   - Open: https://railway.app/dashboard
   - Sign in if needed

2. **Select or Create Project**
   - If you have existing project: Click on it
   - If not: Click **+ New Project**

3. **Create New Service**
   - Click **+ New** button
   - Select **Empty Service** (we'll configure it manually)

**✅ Verify:** Service created and shows in your project

**Status:** [ ] Complete - Service created

---

## ✅ **STEP 2.2: Configure Service - Docker Image**

### **Action:**

1. **Click on the new service** (probably named "Empty Service")

2. **Go to Settings Tab**

3. **Find "Source" or "Deploy" section**

4. **Set Deployment Method:**
   - Option A: **Docker Hub**
     - Image: `hummingbot/hummingbot-api:latest`
   - Option B: **GitHub** (if you have hummingbot-api repo)
     - Connect repository
     - Railway will use Dockerfile

**Recommended:** Use Docker Hub image (simpler)

**✅ Verify:** Service configured with Docker image

**Status:** [ ] Complete - Docker image configured

---

## ✅ **STEP 2.3: Add Postgres Database**

### **Action:**

1. **In Railway Dashboard** (same project)

2. **Click + New** → **Database** → **Add Postgres**

3. **Wait for Postgres to deploy**

4. **Get Connection String:**
   - Click on Postgres service
   - Go to **Variables** tab
   - Find `DATABASE_URL` or `POSTGRES_URL`
   - Copy the connection string

**Example format:**
```
postgresql://postgres:password@containers-us-west-xxx.railway.app:5432/railway
```

**✅ Verify:** Postgres deployed, connection string copied

**Status:** [ ] Complete - Postgres added

---

## ✅ **STEP 2.4: Configure Port**

### **Action:**

1. **Go to Hummingbot API service**

2. **Settings** → **Networking** tab

3. **Add Port:**
   - Port: `8000`
   - Protocol: `HTTP`

**OR Railway may auto-detect port 8000**

**✅ Verify:** Port 8000 configured

**Status:** [ ] Complete - Port configured

---

## ✅ **STEP 2.5: Set Environment Variables**

### **Action:**

1. **Go to Hummingbot API service**

2. **Variables** tab

3. **Add these variables one by one:**

```bash
# API Authentication
USERNAME=admin
PASSWORD=admin
CONFIG_PASSWORD=admin

# Database (use Railway Postgres connection string)
DATABASE_URL=<paste-postgres-connection-string-from-step-2.3>
# Format: postgresql+asyncpg://user:pass@host:port/dbname

# Broker (can use localhost for now, or skip if not needed)
BROKER_HOST=localhost
BROKER_USERNAME=admin
BROKER_PASSWORD=password

# Gateway (optional, can skip for now)
GATEWAY_PASSPHRASE=admin

# Paths
BOTS_PATH=/app/bots
```

**Important:** Replace `<paste-postgres-connection-string>` with actual Postgres URL from Step 2.3

**✅ Verify:** All variables added

**Status:** [ ] Complete - Variables set

---

## ✅ **STEP 2.6: Deploy**

### **Action:**

1. **Railway will auto-deploy** when you add variables

2. **OR manually trigger:**
   - Go to **Deployments** tab
   - Click **Redeploy**

3. **Monitor Deployment:**
   - Watch **Logs** tab
   - Wait for "Deployment successful"
   - Look for any errors

**✅ Verify:** Deployment successful, no errors

**Status:** [ ] Complete - Deployed successfully

---

## ✅ **STEP 2.7: Get Service URL**

### **Action:**

1. **After deployment completes**

2. **Go to Settings** → **Networking**

3. **Find URL:**
   - **Public URL:** `https://hummingbot-api-production.up.railway.app`
   - **Internal URL:** `http://hummingbot-api:8000` (if same project)

4. **Copy the URL**

**For Trading Bridge (same Railway project):**
- Use: `http://hummingbot-api:8000`

**For external testing:**
- Use: Public URL

**✅ Verify:** Have service URL

**Status:** [ ] Complete - URL obtained

---

## ✅ **STEP 2.8: Test Hummingbot on Railway**

### **Action:**

**Test with public URL:**
```bash
curl -u admin:admin https://hummingbot-api-production.up.railway.app/bot-orchestration/status
```

**Expected:**
```json
{"status":"success","data":{}}
```

**✅ Verify:** API responds correctly

**Status:** [ ] Complete - API tested

---

## 📋 **Phase 2 Checklist**

- [ ] Step 2.1: Service created
- [ ] Step 2.2: Docker image configured
- [ ] Step 2.3: Postgres added
- [ ] Step 2.4: Port configured
- [ ] Step 2.5: Environment variables set
- [ ] Step 2.6: Deployed successfully
- [ ] Step 2.7: Service URL obtained
- [ ] Step 2.8: API tested

---

## 🚨 **Troubleshooting**

### **Issue: Service won't deploy**

**Check:**
- Docker image name correct?
- Environment variables set?
- Port configured?
- Check logs for errors

### **Issue: Can't connect to database**

**Check:**
- Postgres connection string correct?
- Postgres service running?
- Database URL format: `postgresql+asyncpg://...`

### **Issue: API not responding**

**Check:**
- Port 8000 exposed?
- Service deployed successfully?
- Check logs for startup errors

---

**Ready to start Step 2.1?** 🚀
