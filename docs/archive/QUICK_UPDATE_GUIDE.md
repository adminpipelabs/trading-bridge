# Quick Update Guide - Coinstore API Key

## You've Created the Key in Coinstore ✅
- Key: `f2f0cb9e70c135e2cddfadc45c818cff`
- IP: `54.205.35.75` ✅

## Now Update Database (Choose One)

### Option 1: Via Frontend/UI (Easiest)
1. Go to your frontend
2. Find Coinstore credentials settings
3. Update:
   - API Key: `f2f0cb9e70c135e2cddfadc45c818cff`
   - API Secret: (enter secret for this key)
4. Save

### Option 2: Via Script
```bash
chmod +x UPDATE_COINSTORE_SIMPLE.sh
./UPDATE_COINSTORE_SIMPLE.sh
```
Then enter:
- API Secret (for the new key)
- Client ID (or wallet address)

### Option 3: Via API Call Directly
```bash
curl -X POST https://trading-bridge-production.up.railway.app/api/cex/credentials \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: <your_client_id>" \
  -d '{
    "exchange": "coinstore",
    "api_key": "f2f0cb9e70c135e2cddfadc45c818cff",
    "api_secret": "<SECRET_FOR_NEW_KEY>"
  }'
```

## What You Need
- ✅ API Key: `f2f0cb9e70c135e2cddfadc45c818cff` (you have this)
- ⚠️ API Secret: Get from Coinstore dashboard for this key
- ⚠️ Client ID: From your account (or use wallet address)

## After Update
1. Wait 1-2 minutes
2. Refresh dashboard
3. Balances should appear! ✅
