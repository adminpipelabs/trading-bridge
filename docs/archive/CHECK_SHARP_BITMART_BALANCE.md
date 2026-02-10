# How to Check Sharp's BitMart Balance

## Method 1: Using API Endpoint (Easiest)

**If you know Sharp's wallet address:**

```bash
curl "https://trading-bridge-production.up.railway.app/api/clients/balances?wallet_address=SHARP_WALLET_ADDRESS" | jq
```

**Or if you know Sharp's account identifier:**

```bash
curl "https://trading-bridge-production.up.railway.app/api/exchange/balance/client_sharp" | jq
```

**Expected response:**
```json
{
  "balances": {
    "bitmart": {
      "SHARP": {
        "total": 1000000.0,
        "free": 1000000.0,
        "used": 0.0
      },
      "USDT": {
        "total": 5000.0,
        "free": 5000.0,
        "used": 0.0
      }
    }
  },
  "total_usdt": 5000.0
}
```

---

## Method 2: Using Python Script (Direct Database Query)

**Prerequisites:**
- Need `DATABASE_URL` from Railway

**Steps:**

1. **Get DATABASE_URL from Railway:**
   - Go to Railway Dashboard → PostgreSQL service → Variables
   - Copy `DATABASE_URL`

2. **Run the script:**
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:port/db"
   python3 check_sharp_bitmart_balance.py
   ```

**Or use the existing script:**
```bash
python3 check_bitmart_balance.py --account client_sharp
# OR
python3 check_bitmart_balance.py --wallet SHARP_WALLET_ADDRESS
```

---

## Method 3: Check Railway Logs

**When the bot runs, it logs balance checks:**

Look for messages like:
```
📊 Volume bot checking balances...
  Base balance: 1000000.0 SHARP
  Quote balance: 5000.0 USDT
```

---

## Method 4: Database Query (Direct)

**In Railway PostgreSQL Query Tab:**

```sql
-- Find Sharp's client
SELECT id, name, account_identifier 
FROM clients 
WHERE name ILIKE '%sharp%' OR account_identifier ILIKE '%sharp%';

-- Check connectors (API keys)
SELECT name, api_key, api_secret, memo
FROM connectors
WHERE client_id = '{client_id_from_above}';
```

**Then test balance using ccxt:**
```python
import ccxt
exchange = ccxt.bitmart({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_API_SECRET',
    'uid': 'YOUR_MEMO'  # If BitMart requires memo
})
balance = exchange.fetch_balance()
print(balance)
```

---

## What to Look For

### ✅ **Balance Found:**
- API returns balances for SHARP and USDT
- Script shows non-zero balances
- Bot can execute trades

### ❌ **No Balance / Error:**
- API returns empty balances
- Script shows "All balances are zero"
- Bot shows "Trade skipped — check balance"

### ⚠️ **API Keys Missing:**
- Script shows "NO CONNECTORS FOUND"
- Need to add BitMart connector via admin UI

---

## Quick Check Commands

**Check via API (if wallet known):**
```bash
# Replace with actual wallet address
WALLET="0x..."
curl -s "https://trading-bridge-production.up.railway.app/api/clients/balances?wallet_address=$WALLET" | \
  jq '.balances.bitmart'
```

**Check via account identifier:**
```bash
curl -s "https://trading-bridge-production.up.railway.app/api/exchange/balance/client_sharp" | \
  jq '.balances.bitmart'
```

---

## Troubleshooting

**If API returns empty:**
1. Check if connectors exist in database
2. Verify API keys are correct
3. Check if BitMart API is accessible
4. Look for errors in Railway logs

**If script fails:**
1. Verify DATABASE_URL is set correctly
2. Check if asyncpg is installed: `pip install asyncpg ccxt`
3. Check database connection
