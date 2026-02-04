# Run Database Migrations — Quick Guide

## ✅ **Method 1: Railway CLI (Recommended)**

If you're in the Railway project directory:

```bash
cd /Users/mikaelo/trading-bridge
railway link  # Link to Railway project (if not already linked)
railway run python scripts/run_migrations.py
```

Or directly with psql:

```bash
railway run psql < migrations/COMPLETE_SETUP.sql
```

---

## ✅ **Method 2: Python Script with DATABASE_URL**

Get DATABASE_URL from Railway Dashboard → PostgreSQL → Variables, then:

```bash
export DATABASE_URL="postgresql://postgres:password@host:port/database"
python3 scripts/run_migrations.py
```

---

## ✅ **Method 3: Simple Shell Script**

```bash
./run_migrations_simple.sh
```

This tries Railway CLI first, then falls back to Python script.

---

## ✅ **Method 4: Manual (Railway Dashboard)**

1. Railway Dashboard → PostgreSQL → Query tab
2. Copy contents of `migrations/COMPLETE_SETUP.sql`
3. Paste → Run

---

## 🧪 **Verify Migrations**

After running, verify with:

```bash
railway run psql -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'bots' AND column_name = 'health_status';"
railway run psql -c "SELECT table_name FROM information_schema.tables WHERE table_name = 'trading_keys';"
railway run psql -c "SELECT id, name, account_identifier, role FROM clients LIMIT 5;"
```

---

**Choose the method that works best for your setup!**
