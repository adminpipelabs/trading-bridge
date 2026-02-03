# Quick Start Setup — Private Key Handling

## ✅ Ready to Deploy

All backend code is complete and pushed. Follow these steps to enable the features:

---

## Step 1: Database Migration (5 minutes)

### Copy & Paste to Railway

1. **Open file:** `migrations/COPY_THIS_TO_RAILWAY.sql`
2. **Copy entire contents**
3. **Go to Railway Dashboard:**
   - Select `trading-bridge` project
   - Click **PostgreSQL** service
   - Click **"Query"** tab
   - Paste SQL
   - Click **"Run"**

**✅ Done when:** Verification query returns `bot_health_logs` and `trading_keys` tables

---

## Step 2: Set ENCRYPTION_KEY (2 minutes)

### Option A: Use Generated Key

```bash
# Already generated for you:
ENCRYPTION_KEY=OmVb_VCQKFxBFosHOUcMhYmu5Dc3LFHZtuvcqJ4mdqs=

# Set in Railway:
railway variables set ENCRYPTION_KEY='OmVb_VCQKFxBFosHOUcMhYmu5Dc3LFHZtuvcqJ4mdqs='
```

### Option B: Generate New Key

```bash
# Generate
./scripts/setup_encryption_key.sh

# Or manually:
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Then set in Railway Dashboard → Variables → Add Variable
```

**✅ Done when:** Variable appears in Railway Dashboard → Variables

---

## Step 3: Verify (1 minute)

### Check Migration

Run in Railway PostgreSQL Query tab:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('bot_health_logs', 'trading_keys');
```

Should return 2 rows.

### Check Backend

```bash
curl https://trading-bridge-production.up.railway.app/health
```

Should return: `{"status":"healthy",...}`

---

## 🎉 That's It!

Both options are now enabled:

### Option 1: Admin Inputs Key
- Admin uses `POST /bots/create` with `wallets` array
- Keys stored in both `trading_keys` and `bot_wallets`
- Works immediately after setup

### Option 2: Client Self-Service
- Client uses `POST /clients/{id}/setup-bot`
- Keys stored securely, encrypted
- Client can rotate/revoke anytime

---

## 📋 Files Created

- ✅ `migrations/COPY_THIS_TO_RAILWAY.sql` - Migration script
- ✅ `scripts/setup_encryption_key.sh` - Key generation script
- ✅ `SETUP_INSTRUCTIONS.md` - Detailed instructions
- ✅ `IMPLEMENTATION_STATUS.md` - Full status report

---

## 🆘 Need Help?

See `SETUP_INSTRUCTIONS.md` for detailed troubleshooting.
