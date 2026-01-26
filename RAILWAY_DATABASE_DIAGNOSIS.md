# Railway PostgreSQL Connection - Diagnosis Report

**Date:** 2026-01-26  
**Purpose:** Diagnose and fix PostgreSQL connection for trading-bridge

---

## 🔍 **Current Status Check**

### **Step 1: Health Endpoint**

**Command:**
```bash
curl https://trading-bridge-production.up.railway.app/health
```

**Current Result:**
```json
{
  "status": "healthy",
  "service": "Trading Bridge",
  "database": "unavailable"
}
```

**Status:** ❌ Database not connected

---

### **Step 2: Clients Endpoint**

**Command:**
```bash
curl https://trading-bridge-production.up.railway.app/clients
```

**Current Result:**
```json
{
  "detail": "Database not available. Set DATABASE_URL environment variable."
}
```

**Status:** ❌ Database connection not configured

---

## 📋 **Action Required**

### **Step 1: Check DATABASE_URL in Railway**

**In Railway Dashboard:**

1. Go to: https://railway.app/dashboard
2. Open your project
3. Click on **trading-bridge** service
4. Click **Variables** tab
5. Look for `DATABASE_URL`

**Report back:**
- [ ] DATABASE_URL exists? (Yes/No)
- [ ] If yes, what's the format? (First 30 chars: `postgresql://postgres:xxx...`)

---

### **Step 2: Link PostgreSQL Service**

**If DATABASE_URL is missing:**

1. In Railway Dashboard → **trading-bridge** → **Variables**
2. Click **"New Variable"** or **"Add Variable"**
3. Click **"Add Reference"** (link icon or dropdown)
4. Select **Postgres** service
5. Select **DATABASE_URL** variable
6. Click **Add**

**Expected result:** Variable appears as `${{Postgres.DATABASE_URL}}` or similar

**Alternative (if reference doesn't work):**
1. Click on **Postgres** service
2. Go to **Variables** or **Connect** tab
3. Copy the `DATABASE_URL` value
4. Go to **trading-bridge** → **Variables**
5. Add: Name=`DATABASE_URL`, Value=(paste URL)

---

### **Step 3: Verify DATABASE_URL Format**

**Correct format examples:**
```
postgresql://postgres:password@host:port/database
postgres://postgres:password@monorail.proxy.rlwy.net:12345/railway
```

**Check:**
- ✅ Starts with `postgres://` or `postgresql://`
- ✅ Has username (`postgres`)
- ✅ Has password (long string)
- ✅ Has host (`.railway.app` or `.rlwy.net`)
- ✅ Has port (`:5432` or similar)
- ✅ Has database name (`/railway`)

---

### **Step 4: Redeploy Trading Bridge**

**After setting DATABASE_URL:**

1. Railway Dashboard → **trading-bridge** → **Deployments**
2. Click **"Redeploy"** on latest deployment
3. Wait 1-2 minutes

**Or:** Push any commit to trigger auto-deploy

---

### **Step 5: Check Deployment Logs**

**After redeploy, check logs:**

1. Railway Dashboard → **trading-bridge** → **Deployments**
2. Click latest deployment
3. Look for these messages:

**Success:**
```
Initializing database...
Database tables created/verified successfully
Database initialized successfully
INFO: Application startup complete
```

**Errors to watch for:**
```
Connection refused
Authentication failed
OperationalError
Failed to create database engine
```

---

### **Step 6: Verify Connection**

**After redeploy, run:**

```bash
# Health check
curl https://trading-bridge-production.up.railway.app/health
```

**Expected (working):**
```json
{
  "status": "healthy",
  "service": "Trading Bridge",
  "database": "postgresql"
}
```

```bash
# Clients endpoint
curl https://trading-bridge-production.up.railway.app/clients
```

**Expected (working):**
```json
{
  "clients": []
}
```

---

## 🐛 **Troubleshooting**

### **Issue: DATABASE_URL not showing**

**Check:**
- PostgreSQL service exists in Railway
- Service is running (green status)
- Try manual copy method

**Fix:**
- Use "Add Reference" method first
- If that fails, manually copy DATABASE_URL from Postgres service

---

### **Issue: Connection refused**

**Check:**
- PostgreSQL service is running
- Check PostgreSQL logs for errors

**Fix:**
- Restart PostgreSQL service
- Verify DATABASE_URL format is correct
- Redeploy trading-bridge

---

### **Issue: Authentication failed**

**Check:**
- DATABASE_URL format is correct
- Password hasn't changed

**Fix:**
- Re-copy DATABASE_URL from Postgres service
- Verify format matches expected pattern
- Redeploy trading-bridge

---

### **Issue: Tables don't exist**

**Check:**
- Deployment logs show `init_db()` running
- No errors during database initialization

**Fix:**
- Check `app/main.py` lifespan event calls `init_db()`
- Check deployment logs for initialization errors
- Verify DATABASE_URL is accessible

---

## 📊 **Report Template**

**Please fill out:**

1. **Is DATABASE_URL set?** (Yes/No)
   - If yes, format: `postgresql://postgres:xxx...` (first 30 chars)

2. **Health endpoint:**
```bash
curl https://trading-bridge-production.up.railway.app/health
```
   - Result: (paste JSON)

3. **Clients endpoint:**
```bash
curl https://trading-bridge-production.up.railway.app/clients
```
   - Result: (paste JSON)

4. **Deployment logs:**
   - Any errors? (paste error message)
   - See "Database initialized successfully"? (Yes/No)

5. **PostgreSQL service status:**
   - Running? (Yes/No)
   - Any errors in logs? (Yes/No)

---

## ✅ **Success Criteria**

**Connection is working when:**

- ✅ Health endpoint shows `"database": "postgresql"`
- ✅ Clients endpoint returns `{"clients": []}` (no errors)
- ✅ Deployment logs show "Database initialized successfully"
- ✅ Can create client and it persists
- ✅ Data survives redeploy

---

**Follow these steps and report back with the results!** 🚀
