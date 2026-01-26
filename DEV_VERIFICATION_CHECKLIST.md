# Dev Verification Checklist - PostgreSQL Connection

**Date:** 2026-01-26  
**Purpose:** Verify trading-bridge is connected to PostgreSQL and working correctly

---

## ✅ **Step 1: Check DATABASE_URL is Set**

**In Railway Dashboard:**

1. Go to: https://railway.app/dashboard
2. Open your project
3. Click on **trading-bridge** service
4. Click **Variables** tab
5. Look for `DATABASE_URL`

**Expected:**
- ✅ Variable exists
- ✅ Value starts with `postgresql://` or `postgres://`
- ✅ Contains host, port, database name

**If missing:** Link Postgres service (see `LINK_EXISTING_POSTGRES.md`)

---

## ✅ **Step 2: Check Health Endpoint**

**Run:**
```bash
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

**If shows `"database": "unavailable"`:**
- DATABASE_URL not set or incorrect
- Check Railway variables
- Check deployment logs for connection errors

---

## ✅ **Step 3: Check Database Initialization**

**Check deployment logs:**

1. Railway Dashboard → **trading-bridge** → **Deployments**
2. Click latest deployment
3. Look for these log messages:

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

## ✅ **Step 4: Test Clients Endpoint**

**Run:**
```bash
curl https://trading-bridge-production.up.railway.app/clients
```

**Expected (working):**
```json
{
  "clients": []
}
```

**If error:**
```json
{
  "detail": "Database not available. Set DATABASE_URL environment variable."
}
```
→ DATABASE_URL not set or connection failed

---

## ✅ **Step 5: Test Create Client**

**Run:**
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/clients/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Client",
    "account_identifier": "test_client",
    "wallets": [{"chain": "evm", "address": "0x1234567890123456789012345678901234567890"}]
  }'
```

**Expected (working):**
```json
{
  "id": "uuid-here",
  "name": "Test Client",
  "account_identifier": "test_client",
  "wallets": [...],
  "connectors": [],
  "created_at": "2026-01-26T...",
  "updated_at": "2026-01-26T..."
}
```

**Then verify it persists:**
```bash
curl https://trading-bridge-production.up.railway.app/clients
```

**Expected:** Should see the test client in the list

---

## ✅ **Step 6: Test Bots Endpoint**

**Run:**
```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Expected (working):**
```json
{
  "bots": []
}
```

**If error:** Check deployment logs for database connection issues

---

## ✅ **Step 7: Test Persistence (Critical)**

**After creating a client/bot:**

1. **Redeploy trading-bridge:**
   - Railway Dashboard → **trading-bridge** → **Deployments** → **Redeploy**
   - Wait 1-2 minutes

2. **Check if data survived:**
```bash
curl https://trading-bridge-production.up.railway.app/clients
curl https://trading-bridge-production.up.railway.app/bots
```

**Expected:** Data should still be there (not empty arrays)

**If data is lost:**
- Database connection is not working
- Tables not being created
- Check deployment logs for `init_db()` errors

---

## ✅ **Step 8: Check Database Tables**

**If you have direct database access:**

1. Connect to PostgreSQL (from Railway Postgres service)
2. Run:
```sql
\dt
```

**Expected tables:**
- `clients`
- `wallets`
- `connectors`
- `bots`

**If tables missing:**
- `init_db()` not running
- Check deployment logs
- Check `app/main.py` lifespan event

---

## 🐛 **Common Issues & Fixes**

| Issue | Check | Fix |
|-------|-------|-----|
| `"database": "unavailable"` | DATABASE_URL variable | Link Postgres service in Railway |
| `Connection refused` | Postgres service running? | Restart Postgres service |
| `Authentication failed` | DATABASE_URL format | Re-copy from Postgres service |
| `Tables don't exist` | Deployment logs | Check `init_db()` is called |
| Data lost on redeploy | Persistence test | Verify DATABASE_URL is set correctly |

---

## 📊 **Verification Summary**

**Fill this out:**

- [ ] DATABASE_URL is set in Railway
- [ ] Health endpoint shows `"database": "postgresql"`
- [ ] Deployment logs show "Database initialized successfully"
- [ ] Clients endpoint returns `{"clients": []}` (no errors)
- [ ] Can create client successfully
- [ ] Can list clients after creation
- [ ] Bots endpoint works
- [ ] Data persists after redeploy

**If all checked:** ✅ PostgreSQL connection is working correctly

**If any unchecked:** See "Common Issues & Fixes" above

---

## 🎯 **Next Steps After Verification**

**If everything works:**

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
    "client_id": "CLIENT_ID_FROM_STEP_1",
    "name": "Sharp Spread",
    "account": "client_sharp",
    "connector": "bitmart",
    "pair": "SHARP/USDT",
    "strategy": "spread",
    "config": {"bid_spread": 0.003, "ask_spread": 0.003, "order_amount": 1600}
  }'
```

3. **Test client dashboard:**
   - Log in as client with wallet `0x6CC52d4b397E0DdFDcd1ecbB37902003C4801685`
   - Should see "Sharp Foundation" welcome
   - Should see "Sharp Spread" bot in "My Bots"

---

**Run through this checklist and report any issues found.** 🚀
