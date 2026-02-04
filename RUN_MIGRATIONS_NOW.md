# Run PostgreSQL Migrations on Railway

**Recommended Method:** Python script (handles dependencies automatically)

---

## 🚀 **Run Migrations (Recommended)**

### **Via Railway CLI:**
```bash
railway run python railway_migrate.py
```

### **Via Railway Dashboard:**
1. Go to Railway Dashboard → **trading-bridge** service
2. Click **"Deployments"** tab
3. Click **"..."** (three dots) on latest deployment → **"Run Command"**
4. Enter: `python railway_migrate.py`
5. Click **"Run"**

---

## 🚀 **Alternative: PostgreSQL Query Tab**

1. Go to Railway Dashboard → **PostgreSQL** service
2. Click **"Query"** tab
3. Copy entire contents of `migrations/COMPLETE_SETUP.sql`
4. Paste into query editor
5. Click **"Execute"**

---

## ✅ **What Gets Migrated**

- ✅ Bot health monitor columns (`health_status`, `reported_status`, etc.)
- ✅ `bot_health_logs` table
- ✅ `trading_keys` table (encrypted key storage)
- ✅ Client roles fix (`admin` vs `client`)

---

## 🔍 **Verification**

After running migrations, verify with:

```sql
-- Check health columns
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'bots' 
AND column_name IN ('health_status', 'reported_status', 'last_trade_time');

-- Check trading_keys table
SELECT table_name FROM information_schema.tables WHERE table_name = 'trading_keys';

-- Check client roles
SELECT id, name, account_identifier, role FROM clients;
```

---

**Scripts ready:** `run_migrations.sh` and `railway_migrate.py`
