# Bot Health Monitor — Deployment Summary

## ✅ Code Changes Completed

All code changes have been implemented and are ready for deployment.

### 1. Main Application (`app/main.py`)
- ✅ Added `asyncpg` import for async database connection pool
- ✅ Added `health_router` import
- ✅ Created asyncpg connection pool in `lifespan` function
- ✅ Started `BotHealthMonitor` service on startup
- ✅ Registered health routes: `app.include_router(health_router)`
- ✅ Properly shutdown health monitor and close connection pool on app shutdown

### 2. Bot Routes (`app/bot_routes.py`)
- ✅ Updated `start_bot` endpoint to set `reported_status = 'running'` when starting
- ✅ Updated `stop_bot` endpoint to set `reported_status = 'stopped'` and `health_status = 'stopped'` when stopping
- ✅ Uses raw SQL to update health columns (gracefully handles case where migration hasn't run yet)

### 3. Dependencies (`requirements.txt`)
- ✅ `httpx>=0.25.0` already present (required for Solana health checks)

### 4. Migration File (`migrations/add_bot_health_tracking.sql`)
- ✅ Migration SQL file exists and is ready to run

---

## 📋 Deployment Steps

### Step 1: Run Database Migration
Execute the SQL migration against your Railway PostgreSQL database:

```sql
-- File: migrations/add_bot_health_tracking.sql
-- Run via Railway Query tab, psql, or any DB client
```

**Note:** The migration uses `VARCHAR(255)` for `bot_id` to match the UUID/String format used in the `bots` table.

### Step 2: Push Code to GitHub
```bash
git add .
git commit -m "feat: wire bot health monitor into main.py"
git push origin main
```

Railway should auto-deploy from the `main` branch.

### Step 3: Verify Deployment
After Railway redeploys, test the endpoints:

```bash
# Health summary for all bots
curl https://trading-bridge-production.up.railway.app/bots/health/summary

# Specific bot health (replace with actual bot ID)
curl https://trading-bridge-production.up.railway.app/bots/1/health

# Force immediate check
curl -X POST https://trading-bridge-production.up.railway.app/bots/1/health/check

# Check Solana bot balance
curl https://trading-bridge-production.up.railway.app/bots/{bot_id}/balance/solana
```

---

## 🔍 How It Works

1. **Startup**: The health monitor starts automatically when the app starts
2. **Monitoring Loop**: Every 5 minutes, checks all bots with `reported_status = 'running'`
3. **CEX Bots** (BitMart/Sharp): Checks recent trades via ccxt + wallet balance
4. **Solana Bots** (Lynk/Jupiter): Checks on-chain transactions + SOL/token balances via Solana RPC
5. **Status Updates**:
   - No trades in 30 min → `health_status = 'stale'`
   - No trades in 2 hours → `health_status = 'stopped'`
   - No funds → `health_status = 'stopped'` with reason "NO FUNDS"
6. **Logging**: All status changes logged to `bot_health_logs` table

---

## 📊 New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/bots/{id}/health` | GET | Get health status for one bot |
| `/bots/{id}/health/check` | POST | Force immediate health check |
| `/bots/health/summary` | GET | Overview of all bots (counts by status) |
| `/bots/heartbeat` | POST | Webhook for bots to push heartbeats |
| `/bots/{id}/health/history` | GET | Audit trail of health checks |
| `/bots/{id}/balance` | GET | CEX bot wallet balance |
| `/bots/{id}/balance/solana` | GET | Solana bot on-chain balance |

---

## ⚙️ Configuration

Health check settings are in `app/bot_health.py`:

- `HEALTH_CHECK_INTERVAL_SECONDS = 300` (5 minutes)
- `STALE_THRESHOLD_MINUTES = 30`
- `STOPPED_THRESHOLD_MINUTES = 120` (2 hours)

Adjust these if needed for low-volume pairs.

---

## 🐛 Troubleshooting

### Health Monitor Not Starting
- Check Railway logs for asyncpg connection errors
- Verify `DATABASE_URL` is set correctly
- Ensure migration has been run (columns must exist)

### Migration Fails
- Check that `bots` table exists before running migration
- Verify `bots.id` column type matches `VARCHAR(255)` (should be UUID/String)

### Health Checks Not Working
- Verify bots have `reported_status = 'running'` (set when starting via API)
- Check that connectors have valid `api_key` and `api_secret` for CEX bots
- For Solana bots, ensure `config` has `base_mint` and wallets table has addresses

---

## 📝 Notes

- The health monitor uses asyncpg for async database access (separate from SQLAlchemy sync pool)
- Health columns are updated via raw SQL to handle cases where migration hasn't run
- Bot start/stop endpoints gracefully handle missing health columns
- All health status changes are logged for audit trail
