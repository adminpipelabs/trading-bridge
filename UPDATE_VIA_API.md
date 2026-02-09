# Update Coinstore Key via API

## Quick Update via API Endpoint

Since you've created the "second key" (`f2f0cb9e70c135e2cddfadc45c818cff`) in Coinstore, update the database via API:

### Option 1: Via Frontend/UI
1. Go to your frontend
2. Navigate to Coinstore credentials settings
3. Update API key to: `f2f0cb9e70c135e2cddfadc45c818cff`
4. Enter the secret for this key
5. Save

### Option 2: Via API Call

```bash
curl -X POST https://trading-bridge-production.up.railway.app/api/cex/credentials \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: <your_client_id>" \
  -d '{
    "exchange": "coinstore",
    "api_key": "f2f0cb9e70c135e2cddfadc45c818cff",
    "api_secret": "<SECRET_FOR_SECOND_KEY>"
  }'
```

### Option 3: Run Update Script

```bash
export DATABASE_URL="your_database_url"
export COINSTORE_NEW_SECRET="secret_for_second_key"
python3 UPDATE_COINSTORE_KEY_NOW.py
```

## What This Does

- Updates `exchange_credentials` table
- Uses new key: `f2f0cb9e70c135e2cddfadc45c818cff`
- IP whitelist: `54.205.35.75` (matches Railway)
- Balances should work immediately after update
