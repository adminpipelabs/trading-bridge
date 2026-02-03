# Client Self-Service Backend — Deployment Guide

## ✅ Code Implementation Complete

All backend endpoints have been implemented and are ready for deployment.

---

## Files Created

1. **`app/client_setup_routes.py`** ✅
   - All 4 endpoints implemented
   - Uses SQLAlchemy (matches existing codebase pattern)
   - Fernet encryption for private keys
   - Integrates with bot_runner for bot creation/starting

2. **`migrations/create_trading_keys.sql`** ✅
   - Creates `trading_keys` table
   - Indexes for performance
   - Comments for documentation

3. **`scripts/generate_encryption_key.py`** ✅
   - Helper script to generate encryption key

4. **`app/main.py`** ✅ MODIFIED
   - Route registered: `app.include_router(client_setup_router)`

---

## Deployment Steps

### Step 1: Generate Encryption Key

**Option A: Using the script**
```bash
cd /Users/mikaelo/trading-bridge
python3 scripts/generate_encryption_key.py
```

**Option B: One-liner**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**⚠️ CRITICAL: Back up the generated key securely!**
- Store in password manager
- Save in secure vault
- If lost, all encrypted keys become unrecoverable

---

### Step 2: Add Railway Environment Variable

1. Go to Railway Dashboard → trading-bridge service → Variables
2. Click "New Variable"
3. Add:
   - **Key:** `ENCRYPTION_KEY`
   - **Value:** (paste the key from Step 1)
4. Click "Add"

---

### Step 3: Run Database Migration

Execute the SQL migration against Railway PostgreSQL:

**Option A: Railway Query Tab**
1. Railway Dashboard → PostgreSQL service → Query tab
2. Copy/paste contents of `migrations/create_trading_keys.sql`
3. Execute

**Option B: psql**
```bash
psql $DATABASE_URL -f migrations/create_trading_keys.sql
```

**Option C: Any PostgreSQL client**
Run the SQL from `migrations/create_trading_keys.sql`

---

### Step 4: Push Code to GitHub

```bash
cd /Users/mikaelo/trading-bridge
git add app/client_setup_routes.py migrations/create_trading_keys.sql scripts/generate_encryption_key.py app/main.py
git commit -m "feat: add client self-service bot setup endpoints

- Add POST /clients/{id}/setup-bot - Client submits private key + config
- Add GET /clients/{id}/bot-options - Returns available bot types
- Add PUT /clients/{id}/rotate-key - Client rotates private key
- Add DELETE /clients/{id}/revoke-key - Client revokes key, stops bots
- Fernet encryption for private keys (AES-256)
- Integrates with bot_runner for bot creation/starting
- Migration: create trading_keys table"
git push origin main
```

Railway will auto-deploy.

---

### Step 5: Verify Deployment

After Railway finishes deploying, test the endpoints:

```bash
# Replace CLIENT_ID with actual client ID
CLIENT_ID="d258b6d3-cf74-4b0e-bc1a-be7707939231"

# 1. Get bot options
curl "https://trading-bridge-production.up.railway.app/clients/${CLIENT_ID}/bot-options"

# Expected: Returns available bot types for client's chain
```

**Test bot setup** (use a TEST key, not real):
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/clients/${CLIENT_ID}/setup-bot" \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: YOUR_WALLET_ADDRESS" \
  -d '{
    "bot_type": "volume",
    "private_key": "TEST_KEY_DO_NOT_USE_REAL",
    "config": {
      "base_mint": "HZG1RVn4zcRM7zEFEVGYPGoPzPAWAj2AAdvQivfmLYNK",
      "quote_mint": "So11111111111111111111111111111111111111112",
      "daily_volume_usd": 5000,
      "min_trade_usd": 10,
      "max_trade_usd": 25,
      "interval_min_seconds": 900,
      "interval_max_seconds": 2700,
      "slippage_bps": 50
    }
  }'
```

---

## Security Checklist

- [x] `cryptography>=41.0.0` in requirements.txt
- [ ] `ENCRYPTION_KEY` set in Railway env vars
- [ ] `ENCRYPTION_KEY` backed up securely
- [ ] `trading_keys` table created in PostgreSQL
- [x] Route registered in main.py
- [x] No API endpoint returns encrypted_key or decrypted key
- [ ] Consider adding rate limiting (optional but recommended)

---

## How It Works

### Encryption Flow
```
Client submits private_key
        │
        ▼
encrypt_key() → Fernet.encrypt() → encrypted_key (TEXT)
        │
        ▼
Stored in trading_keys.encrypted_key
        │
        ▼
Never returned in API responses
```

### Bot Setup Flow
```
POST /clients/{id}/setup-bot
        │
        ├── Validate client exists
        ├── Derive wallet address (Solana)
        ├── Encrypt private_key
        ├── Store in trading_keys table
        ├── Create Bot record
        ├── Add wallet to bot_wallets table
        └── Start bot via bot_runner
```

### Key Rotation Flow
```
PUT /clients/{id}/rotate-key
        │
        ├── Encrypt new private_key
        ├── Update trading_keys.encrypted_key
        └── Update all bot_wallets.encrypted_private_key
```

### Key Revocation Flow
```
DELETE /clients/{id}/revoke-key
        │
        ├── Stop all client's bots
        └── Delete from trading_keys table
```

---

## API Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/clients/{id}/bot-options` | GET | Optional | Get available bot types |
| `/clients/{id}/setup-bot` | POST | Required | Create bot with encrypted key |
| `/clients/{id}/rotate-key` | PUT | Required | Rotate private key |
| `/clients/{id}/revoke-key` | DELETE | Required | Revoke key, stop bots |

**Auth:** Uses existing `X-Wallet-Address` header or JWT token (same as other endpoints)

---

## Error Handling

- **404:** Client not found
- **400:** Invalid bot_type, invalid private key format
- **500:** Encryption failure, database error
- **Security:** Private keys never returned in responses

---

## Integration with Frontend

The frontend components are already implemented:
- `ClientBotSetup.jsx` - Calls `/clients/{id}/setup-bot`
- `KeyManagement.jsx` - Calls `/clients/{id}/rotate-key` and `/clients/{id}/revoke-key`

Once backend is deployed and migration run, the full flow will work end-to-end.

---

## Troubleshooting

### "Encryption not configured"
- Check `ENCRYPTION_KEY` is set in Railway env vars
- Verify key is valid Fernet key (base64, 44 chars)

### "No trading key found"
- Client hasn't set up a bot yet
- Call `/clients/{id}/setup-bot` first

### "Failed to derive wallet address"
- Invalid Solana private key format
- Should be base58 encoded, 32 or 64 bytes when decoded

### Database errors
- Verify `trading_keys` table exists (run migration)
- Check PostgreSQL connection in Railway logs

---

## Next Steps After Deployment

1. ✅ Backend endpoints deployed
2. ✅ Frontend components ready (already pushed)
3. ⏳ Test end-to-end flow:
   - Client logs in
   - Client sets up bot via wizard
   - Bot appears in list with health status
   - Client can rotate/revoke key

All code is ready. Just need to:
1. Generate and set `ENCRYPTION_KEY`
2. Run database migration
3. Push code (if not already pushed)
