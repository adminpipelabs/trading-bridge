# Run Database Migration - Add Frontend Columns

**Date:** 2026-01-27  
**Purpose:** Add missing columns to `clients` table for Pipe Labs backend compatibility

---

## 🎯 **Quick Fix**

Run the SQL migration to add missing columns to the `clients` table.

---

## ✅ **Option 1: Railway Query Console (Easiest)**

1. **Railway Dashboard** → Click **PostgreSQL** service
2. Click **"Data"** tab or **"Query"** tab
3. **Copy and paste** this SQL:

```sql
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(100);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_type VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS tier VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'client';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}';
```

4. Click **"Run"** or **"Execute"**
5. Should see: `ALTER TABLE` (8 rows affected)

---

## ✅ **Option 2: Via psql CLI**

```bash
# Get connection string from Railway PostgreSQL Variables
# Format: postgresql://postgres:PASSWORD@postgres.railway.internal:5432/railway

psql "postgresql://postgres:YOUR_PASSWORD@postgres.railway.internal:5432/railway"

# Then run:
\i migrations/add_frontend_columns.sql

# Or paste the ALTER TABLE statements directly
```

---

## ✅ **Option 3: Via Railway CLI**

```bash
railway connect postgres
# Then paste the SQL statements
```

---

## 🔍 **Verify Migration**

After running, verify columns exist:

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'clients'
ORDER BY ordinal_position;
```

**Expected columns:**
- `id`, `name`, `account_identifier`
- `wallet_address`, `wallet_type`, `email`, `password_hash`
- `status`, `tier`, `role`, `settings`
- `created_at`, `updated_at`

---

## 🔄 **After Migration**

1. **Restart Pipe Labs backend** in Railway:
   - Railway Dashboard → `backend-pipelabs-dashboard` → **Deployments** → **Redeploy**
   - (This refreshes DB connection/schema cache)

2. **Test admin login:**
   - Should load without `wallet_address does not exist` error

---

## 📋 **What This Does**

- ✅ Adds 8 missing columns to `clients` table
- ✅ Sets defaults: `status='active'`, `role='client'`, `settings='{}'`
- ✅ Uses `IF NOT EXISTS` to prevent errors if columns already exist
- ✅ Adds indexes for performance

---

**Run the SQL migration, then restart Pipe Labs backend!**
