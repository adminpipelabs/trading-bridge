# Link Existing PostgreSQL to Trading Bridge

**Goal:** Connect trading-bridge to the existing Postgres service in Railway (no new services needed)

---

## ✅ **What You Have**

From Railway dashboard:
- ✅ **Postgres** service (Online) - Already exists
- ✅ **trading-bridge** service (Online) - Needs to connect to Postgres

---

## 🔗 **Step 1: Link Postgres to Trading Bridge**

**In Railway Dashboard:**

1. **Click on `trading-bridge` service**
2. **Go to Variables tab**
3. **Click "New Variable"**
4. **Click "Add Reference"** (or the link icon)
5. **Select `Postgres` service**
6. **Select `DATABASE_URL` variable**
7. **Click "Add"**

**Result:** Creates a reference variable that Railway resolves automatically.

**Alternative (if reference doesn't work):**
1. Click on **Postgres** service
2. Go to **Variables** or **Connect** tab
3. Copy the `DATABASE_URL` value
4. Go to **trading-bridge** → **Variables**
5. Add: Name=`DATABASE_URL`, Value=(paste the URL)

---

## 🔄 **Step 2: Redeploy**

**After setting DATABASE_URL:**

Railway will auto-redeploy, or:
- Click **trading-bridge** → **Deployments** → **Redeploy**

**Wait:** 1-2 minutes

---

## ✅ **Step 3: Verify**

**Check health:**
```bash
curl https://trading-bridge-production.up.railway.app/health
```

**Expected (working):**
```json
{"status": "healthy", "service": "Trading Bridge", "database": "postgresql"}
```

**Test clients endpoint:**
```bash
curl https://trading-bridge-production.up.railway.app/clients
```

**Expected (working):**
```json
{"clients": []}
```

---

## 🎯 **That's It!**

**No new services needed** - just link the existing Postgres to trading-bridge.

**After connection works:**
- Create Sharp Foundation client
- Create Sharp Spread bot
- Test persistence (redeploy and verify bots still exist)

---

**Total time:** ~2 minutes (just link the variable and redeploy)
