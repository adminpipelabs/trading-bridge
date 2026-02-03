# 🚨 URGENT: Run Database Migrations

## Problem
Bot statuses are stuck showing "running" even when bots have stopped. The health monitor code is deployed but can't work until the database has the new columns.

---

## Quick Start

### Option 1: Railway Dashboard (Easiest)

1. Go to **Railway Dashboard** → **PostgreSQL service** → **Query** tab
2. Open `migrations/run_all_migrations.sql` in this repo
3. Copy the entire contents
4. Paste into Railway Query tab
5. Click **Run** or **Execute**
6. Wait for success message

### Option 2: Command Line (psql)

```bash
# Get DATABASE_URL from Railway
# Then run:
psql $DATABASE_URL -f migrations/run_all_migrations.sql
```

### Option 3: Any PostgreSQL Client

1. Connect to Railway PostgreSQL using connection string from Railway dashboard
2. Open `migrations/run_all_migrations.sql`
3. Execute the entire file

---

## What Gets Created

### Migration 1: Health Monitor
- Adds columns to `bots` table:
  - `health_status` (healthy/stale/stopped/error/unknown)
  - `health_message` (reason for status)
  - `last_trade_time` (when bot last traded)
  - `last_heartbeat` (when bot last sent heartbeat)
  - `reported_status` (what user set it to)
  - `status_updated_at` (when status changed)
- Creates `bot_health_logs` table (audit trail)
- Creates indexes for performance

### Migration 2: Client Self-Service
- Creates `trading_keys` table (encrypted private keys)
- Creates index for lookups

---

## Verify Migrations Ran

After running migrations, execute `migrations/verify_migrations.sql` to check:

```sql
-- Quick check - should return 6 columns
SELECT COUNT(*) 
FROM information_schema.columns 
WHERE table_name = 'bots' 
  AND column_name IN ('health_status', 'health_message', 'last_trade_time', 'reported_status', 'last_heartbeat', 'status_updated_at');
-- Expected: 6

-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('bot_health_logs', 'trading_keys');
-- Expected: bot_health_logs, trading_keys
```

---

## What Happens Next

1. **Immediately after migration:**
   - All bots will have `health_status = 'unknown'`
   - Frontend will show gray "Unknown" badges

2. **Within 5 minutes:**
   - Health monitor runs its first check
   - Checks all bots marked as "running"
   - Updates `health_status` based on actual activity

3. **Expected results:**
   - **Lynk bot** (no trades) → `health_status = 'stopped'` with message "No trades found in last 3 hours"
   - **Sharp bot** (if trading) → `health_status = 'healthy'` or `'stale'`
   - Frontend badges will update automatically

---

## Troubleshooting

### "column already exists" errors
- ✅ **Safe to ignore** - `IF NOT EXISTS` prevents duplicates
- Migration is idempotent (can run multiple times)

### "relation already exists" errors
- ✅ **Safe to ignore** - Tables already created
- Migration is idempotent

### Health status still shows "unknown" after 10 minutes
- Check Railway logs for health monitor errors
- Verify `ENCRYPTION_KEY` is set (if using client self-service)
- Check that health monitor started: Look for "Bot health monitor started" in logs

### Frontend still shows "running"
- Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)
- Check browser console for API errors
- Verify backend returned `health_status` field in `/bots` response

---

## Files

- `migrations/run_all_migrations.sql` - **Run this** (contains both migrations)
- `migrations/verify_migrations.sql` - Verification queries
- `migrations/add_bot_health_tracking.sql` - Health migration only
- `migrations/create_trading_keys.sql` - Trading keys migration only

---

## After Migrations

The health monitor will automatically:
- Check bots every 5 minutes
- Update `health_status` based on trades
- Log changes to `bot_health_logs`
- Show real status in frontend badges

**No restart needed** - migrations are live immediately.
