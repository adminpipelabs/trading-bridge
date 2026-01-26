# Railway PostgreSQL Connection Setup - Step by Step

**Date:** 2026-01-26  
**Goal:** Connect trading-bridge to existing PostgreSQL database in Railway

---

## 🔍 **Step 1: Check Current Status**

**Run this command:**
```bash
curl https://trading-bridge-production.up.railway.app/health
```

**Current result:**
```json
{"status": "healthy", "database": "unavailable"}
```

**This means:** DATABASE_URL is not set or not connected.

---

## 📋 **Step 2: Link PostgreSQL to Trading Bridge**

### **Method A: Add Reference (Recommended)**

1. **Go to Railway Dashboard:**
   - https://railway.app/dashboard
   - Open your project
   - Click on **trading-bridge** service

2. **Add Variable Reference:**
   - Click **Variables** tab
   - Click **"New Variable"** or **"Add Variable"**
   - Click **"Add Reference"** (small link icon or dropdown)
   - Select your **PostgreSQL** service from the list
   - Select **DATABASE_URL** from available variables
   - Click **Add**

**Result:** Creates a reference like `${{Postgres.DATABASE_URL}}`

---

### **Method B: Manual Copy (If Reference Doesn't Work)**

1. **Get DATABASE_URL from PostgreSQL:**
   - Click on **PostgreSQL** service in Railway
   - Click **Variables** tab (or **Connect** tab)
   - Copy the `DATABASE_URL` value
   - Should look like: `postgresql://postgres:xxx@xxx.railway.app:5432/railway`

2. **Add to Trading Bridge:**
   - Go back to **trading-bridge** service
   - Click **Variables** tab
   - Click **"New Variable"**
   - Name: `DATABASE_URL`
   - Value: Paste the connection string
   - Click **Add**

---

## ✅ **Step 3: Verify DATABASE_URL Format**

**Correct format:**
```
postgresql://postgres:password@host:port/database
```

**Examples:**
- `postgresql://postgres:xxx@containers-us-west-xxx.railway.app:5432/railway`
- `postgres://postgres:xxx@monorail.proxy.rlwy.net:12345/railway`

**Check:**
- ✅ Starts with `postgres://` or `postgresql://`
- ✅ Has username (`postgres`)
- ✅ Has password (long string)
- ✅ Has host (`.railway.app` or `.rlwy.net`)
- ✅ Has port (`:5432` or similar)
- ✅ Has database name (`/railway`)

---

## 🔄 **Step 4: Redeploy Trading Bridge**

**After setting DATABASE_URL:**

1. **Option A: Manual Redeploy**
   - Click on **trading-bridge** service
   - Click **Deployments** tab
   - Click **"Redeploy"** on latest deployment

2. **Option B: Trigger via Git**
   - Push any commit (or I can push a dummy commit)
   - Railway auto-deploys

**Wait:** 1-2 minutes for deployment to complete

---

## 🔍 **Step 5: Check Deployment Logs**

**Look for these success messages:**
```
Initializing database...
Database tables created/verified successfully
INFO: Application startup complete
```

**Error messages to watch for:**
```
Connection refused
Authentication failed
Relation does not exist
OperationalError
```

---

## 🧪 **Step 6: Test Connection**

**After redeploy, run:**

```bash
# Health check
curl https://trading-bridge-production.up.railway.app/health
```

**Expected (working):**
```json
{"status": "healthy", "service": "Trading Bridge", "database": "postgresql"}
```

**Expected (not working):**
```json
{"status": "healthy", "service": "Trading Bridge", "database": "unavailable"}
```

```bash
# Test clients endpoint
curl https://trading-bridge-production.up.railway.app/clients
```

**Expected (working):**
```json
{"clients": []}
```

**Expected (error):**
```json
{"detail": "Database not available. Set DATABASE_URL environment variable."}
```

---

## 🐛 **Troubleshooting**

### **Issue: DATABASE_URL not showing in variables**
- Check PostgreSQL service exists in Railway
- Try manual copy method (Method B)
- Verify variable name is exactly `DATABASE_URL` (case-sensitive)

### **Issue: Connection refused**
- Check PostgreSQL service is running (green status)
- Restart PostgreSQL service if needed
- Verify DATABASE_URL format is correct

### **Issue: Authentication failed**
- Re-copy DATABASE_URL (password may have changed)
- Check PostgreSQL service logs for errors

### **Issue: Tables don't exist**
- Check deployment logs for `init_db()` errors
- Verify `init_db()` is called in main.py lifespan
- Check Railway logs for database initialization messages

---

## 📊 **What to Report Back**

**Please provide:**

1. **Is DATABASE_URL set?** (Yes/No)
   - Check: Railway → trading-bridge → Variables → DATABASE_URL

2. **DATABASE_URL format:** (First 30 chars)
   - Example: `postgresql://postgres:xxx...`

3. **Health endpoint:**
```bash
curl https://trading-bridge-production.up.railway.app/health
```

4. **Clients endpoint:**
```bash
curl https://trading-bridge-production.up.railway.app/clients
```

5. **Deployment logs:** (Any errors?)
   - Railway → trading-bridge → Deployments → Latest → Logs

---

## ✅ **Next Steps After Connection Works**

Once database is connected:

1. **Create Sharp Foundation client:**
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/clients/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sharp Foundation",
    "account_identifier": "client_sharp",
    "wallets": [{"chain": "evm", "address": "0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685"}]
  }'
```

2. **Create Sharp Spread bot:**
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/bots/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sharp Spread",
    "account": "client_sharp",
    "connector": "bitmart",
    "pair": "SHARP/USDT",
    "strategy": "spread",
    "config": {"bid_spread": 0.003, "ask_spread": 0.003, "order_amount": 1600}
  }'
```

3. **Test persistence:**
   - Redeploy trading-bridge
   - Verify bots/clients still exist

---

**Follow these steps and report back with the results!** 🚀
