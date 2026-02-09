# Run Database Migration - CEX Volume Bot

## ⚠️ **URGENT: Migration Required**

The `exchange_credentials` table doesn't exist yet. You need to run the migration.

---

## **Option 1: Railway PostgreSQL Query Tab (Recommended)**

1. **Go to Railway Dashboard**
   - Navigate to your PostgreSQL database service
   - Click on **Query** tab

2. **Copy and paste this SQL:**

```sql
-- Exchange credentials table
CREATE TABLE IF NOT EXISTS exchange_credentials (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_secret_encrypted TEXT NOT NULL,
    passphrase_encrypted TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, exchange)
);

CREATE INDEX IF NOT EXISTS idx_exchange_creds_client ON exchange_credentials(client_id);

-- Add exchange, base_asset, quote_asset columns to bots table
ALTER TABLE bots ADD COLUMN IF NOT EXISTS exchange VARCHAR(50);
ALTER TABLE bots ADD COLUMN IF NOT EXISTS base_asset VARCHAR(20);
ALTER TABLE bots ADD COLUMN IF NOT EXISTS quote_asset VARCHAR(20);

-- Trade logs table for CEX bots
CREATE TABLE IF NOT EXISTS trade_logs (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) NOT NULL,
    side VARCHAR(10) NOT NULL,
    amount DECIMAL(20, 8),
    price DECIMAL(20, 8),
    cost_usd DECIMAL(20, 2),
    order_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trade_logs_bot ON trade_logs(bot_id, created_at DESC);
```

3. **Click "Run Query"**

4. **Verify:**
   - Should see "Success" message
   - No errors

---

## **Option 2: Using psql Command Line**

If you have `psql` installed locally:

```bash
# Get DATABASE_URL from Railway
# Then run:
psql $DATABASE_URL < migrations/add_cex_volume_bot.sql
```

---

## **After Migration**

Once the migration is complete:
- ✅ Errors will stop appearing in logs
- ✅ CEX bot runner will work correctly
- ✅ You can add exchange credentials via API
- ✅ CEX volume bots can be created and started

---

## **Verify Migration Worked**

Check Railway logs - you should see:
- ✅ No more "relation exchange_credentials does not exist" errors
- ✅ CEX bot runner running without errors

---

**Status:** ⚠️ **MIGRATION REQUIRED** - Run the SQL above in Railway PostgreSQL Query tab.
