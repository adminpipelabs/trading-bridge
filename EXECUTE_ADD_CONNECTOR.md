# Execute: Add BitMart Connector

## Step 1: Get BitMart Credentials

The credentials are in Hummingbot. You need to get them:

### Option A: From Hummingbot Container (if running locally)
```bash
docker exec -it hummingbot-api cat bots/credentials/client_sharp/connectors/bitmart.yml
```

### Option B: From Hummingbot Files (if accessible)
```bash
cat /path/to/hummingbot/bots/credentials/client_sharp/connectors/bitmart.yml
```

### Option C: From Admin Dashboard
- Check if stored in admin dashboard → Clients → Sharp Foundation → API Keys

---

## Step 2: Execute curl Command

Once you have the credentials, run:

```bash
curl -X PUT \
  "https://trading-bridge-production.up.railway.app/clients/70ab29b1-66ad-4645-aec8-fa2f55abe144/connector" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bitmart",
    "api_key": "PASTE_YOUR_BITMART_API_KEY_HERE",
    "api_secret": "PASTE_YOUR_BITMART_API_SECRET_HERE",
    "memo": "PASTE_YOUR_BITMART_MEMO_HERE"
  }'
```

**Replace**:
- `PASTE_YOUR_BITMART_API_KEY_HERE` → Your actual BitMart API Key
- `PASTE_YOUR_BITMART_API_SECRET_HERE` → Your actual BitMart Secret
- `PASTE_YOUR_BITMART_MEMO_HERE` → Your actual BitMart Memo (if required)

---

## Step 3: Verify Connector Added

```bash
curl https://trading-bridge-production.up.railway.app/clients/70ab29b1-66ad-4645-aec8-fa2f55abe144 | python3 -m json.tool | grep -A 10 connectors
```

**Expected**: Should show connector with `name: "bitmart"`

---

## Step 4: Test Dashboard

```bash
curl https://trading-bridge-production.up.railway.app/api/exchange/dashboard/client_sharp | python3 -m json.tool
```

**Expected**: Should show real balances, trades, P&L:
```json
{
  "balance": {
    "total_usdt": 500.0,
    "balances": [
      {"exchange": "bitmart", "asset": "USDT", "total": 500.0},
      {"exchange": "bitmart", "asset": "SHARP", "total": 1000.0}
    ]
  },
  "pnl": {"total": 150.50},
  "volume": {"traded": 10000.0, "trade_count": 25},
  "recent_trades": [...]
}
```

---

## After Success: Update Admin UI

Once connector is added and dashboard shows data, we need to:

1. **Update Admin UI workflow** to include "Add API Keys" step
2. **Add reminder** when creating clients
3. **Consider auto-sync** from Hummingbot in future

---

## Note

I cannot execute the curl command with real credentials because:
- Credentials are stored in Hummingbot (not accessible to me)
- Security: Credentials should not be exposed in chat/logs

**Please execute the curl command yourself** with the actual BitMart credentials from Hummingbot.
