# Setup Instructions — Private Key Handling

## Step 1: Run Database Migration ⚠️ CRITICAL

### Option A: Railway Dashboard (Recommended)

1. **Open Railway Dashboard**
   - Go to https://railway.app
   - Select your `trading-bridge` project
   - Click on **PostgreSQL** service

2. **Open Query Tab**
   - Click on **"Query"** tab in the PostgreSQL service
   - This opens a SQL editor

3. **Copy & Paste Migration**
   - Open `migrations/COPY_THIS_TO_RAILWAY.sql` in this repo
   - Copy the **entire contents**
   - Paste into the Railway Query editor
   - Click **"Run"** or press `Cmd+Enter` (Mac) / `Ctrl+Enter` (Windows)

4. **Verify Success**
   - You should see "Success" message
   - Run this verification query:
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_name IN ('bot_health_logs', 'trading_keys');
   ```
   - Should return: `bot_health_logs` and `trading_keys`

### Option B: Railway CLI (Alternative)

```bash
# Get DATABASE_URL
railway variables get DATABASE_URL

# Run migration (if you have psql installed locally)
psql $DATABASE_URL -f migrations/COPY_THIS_TO_RAILWAY.sql
```

---

## Step 2: Set ENCRYPTION_KEY ⚠️ CRITICAL

### Option A: Generate & Set via Script

```bash
# Generate key
./scripts/setup_encryption_key.sh

# Copy the generated key, then set in Railway:
railway variables set ENCRYPTION_KEY='<paste-generated-key-here>'
```

### Option B: Manual Generation

```bash
# Generate key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Copy the output, then:
railway variables set ENCRYPTION_KEY='<paste-key-here>'
```

### Option C: Railway Dashboard

1. **Generate Key**
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Add to Railway**
   - Go to Railway Dashboard → `trading-bridge` project
   - Click **"Variables"** tab
   - Click **"New Variable"**
   - Name: `ENCRYPTION_KEY`
   - Value: (paste the generated key)
   - Click **"Add"**

3. **Redeploy** (if needed)
   - Railway will auto-redeploy when you add variables
   - Or manually trigger: Railway Dashboard → Deployments → Redeploy

---

## Step 3: Verify Setup ✅

### Check Migration

Run this in Railway PostgreSQL Query tab:
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('bot_health_logs', 'trading_keys');

-- Check columns exist
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'bots' 
AND column_name IN ('health_status', 'reported_status', 'last_trade_time');
```

### Check ENCRYPTION_KEY

```bash
# Check if variable is set (won't show value for security)
railway variables | grep ENCRYPTION_KEY

# Or check Railway Dashboard → Variables
```

### Test Backend

```bash
# Health check (should work)
curl https://trading-bridge-production.up.railway.app/health

# Should return: {"status":"healthy",...}
```

---

## Step 4: Test Both Options 🧪

### Option 1: Admin Inputs Key

```bash
# Admin creates bot with wallet
curl -X POST https://trading-bridge-production.up.railway.app/bots/create \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: <admin-wallet>" \
  -d '{
    "name": "Test Bot",
    "account": "client_test",
    "bot_type": "volume",
    "config": {"daily_volume_usd": 1000},
    "wallets": [{
      "address": "YourWalletAddress",
      "private_key": "YourPrivateKey"
    }]
  }'
```

### Option 2: Client Self-Service

```bash
# Client sets up bot with their own key
curl -X POST https://trading-bridge-production.up.railway.app/clients/{client_id}/setup-bot \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: <client-wallet>" \
  -d '{
    "bot_type": "volume",
    "private_key": "ClientPrivateKey",
    "config": {"daily_volume_usd": 5000}
  }'
```

---

## Troubleshooting

### Migration Fails

**Error:** `relation "bots" does not exist`
- **Fix:** Make sure you're running against the correct database
- Check DATABASE_URL points to the right PostgreSQL instance

**Error:** `column already exists`
- **Fix:** Migration is idempotent - safe to ignore
- Columns already exist, which is fine

### ENCRYPTION_KEY Not Working

**Error:** `Encryption not configured. Set ENCRYPTION_KEY.`
- **Fix:** Make sure ENCRYPTION_KEY is set in Railway
- Redeploy after setting the variable
- Check Railway logs for errors

### Keys Not Storing

**Error:** `relation "trading_keys" does not exist`
- **Fix:** Run the migration (Step 1)
- Verify table exists with verification query

---

## What Gets Created

### Database Tables

1. **`bot_health_logs`**
   - Stores health check history
   - Used by health monitor

2. **`trading_keys`**
   - Stores encrypted private keys (one per client)
   - Used for key rotation/revocation

### Database Columns (added to `bots` table)

- `health_status` - Current health status
- `health_message` - Health status message
- `last_trade_time` - Last trade timestamp
- `last_heartbeat` - Last heartbeat timestamp
- `reported_status` - User-reported status
- `status_updated_at` - Status update timestamp

---

## Next Steps

After setup is complete:

1. ✅ Test admin flow (create bot with key)
2. ✅ Test client flow (client sets up bot)
3. ✅ Test key rotation
4. ✅ Test key revocation
5. ✅ Verify frontend components work

---

## Support

If you encounter issues:

1. Check Railway logs: `railway logs`
2. Check database connection: Railway Dashboard → PostgreSQL → Query
3. Verify environment variables: Railway Dashboard → Variables
4. Check backend health: `curl https://trading-bridge-production.up.railway.app/health`
