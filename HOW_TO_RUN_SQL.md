# How to Run SQL Migration in Railway

**Quickest way:** Use Railway's web interface (no CLI needed)

---

## ✅ **Method 1: Railway Web Console (Easiest - Recommended)**

1. **Go to Railway Dashboard:** https://railway.app/dashboard
2. **Click on your PostgreSQL service** (the database icon)
3. **Click "Data" tab** or **"Query" tab**
4. **Copy this SQL:**

```sql
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(100);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS wallet_type VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS tier VARCHAR(20);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'client';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}';
ALTER TABLE clients ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
```

5. **Paste into the query box**
6. **Click "Run" or "Execute"**
7. **Done!** Refresh admin page

---

## ✅ **Method 2: Railway CLI (If Installed)**

```bash
# Install Railway CLI first
npm i -g @railway/cli

# Login
railway login

# Connect to PostgreSQL
railway connect postgres

# Then paste the SQL statements
```

---

## ✅ **Method 3: psql (If You Have PostgreSQL Client)**

```bash
# Get DATABASE_URL from Railway PostgreSQL Variables
# Format: postgresql://postgres:PASSWORD@postgres.railway.internal:5432/railway

# Run migration script
psql "postgresql://postgres:YOUR_PASSWORD@postgres.railway.internal:5432/railway" -f fix_clients_table.sql

# Or run the shell script
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@postgres.railway.internal:5432/railway"
./run_migration.sh
```

---

## 🎯 **Recommended: Use Method 1 (Web Console)**

It's the fastest and doesn't require any CLI tools!
