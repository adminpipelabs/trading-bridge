# Add BitMart Connector to Trading-Bridge

## Current Situation

✅ **Connectors exist in Hummingbot** (credentials profile `client_sharp`)  
❌ **Connectors NOT in trading-bridge database**  
❌ **Result**: Dashboard shows empty data

---

## Step 1: Get BitMart Credentials

The credentials are in Hummingbot. Get them from:

**Option A: Hummingbot Credentials File**
```bash
# In Hummingbot container or local files
cat bots/credentials/client_sharp/connectors/bitmart.yml
```

**Option B: Hummingbot API** (if available)
```bash
# Query Hummingbot for credentials
curl -u admin:admin https://hummingbot-api-url/api/credentials/client_sharp
```

**Option C: Admin Dashboard** (if stored there)
- Check admin dashboard → Clients → Sharp Foundation → API Keys

---

## Step 2: Add Connector to Trading-Bridge

```bash
curl -X PUT \
  "https://trading-bridge-production.up.railway.app/clients/70ab29b1-66ad-4645-aec8-fa2f55abe144/connector" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bitmart",
    "api_key": "YOUR_ACTUAL_BITMART_API_KEY",
    "api_secret": "YOUR_ACTUAL_BITMART_API_SECRET",
    "memo": "YOUR_ACTUAL_BITMART_MEMO"
  }'
```

**Replace**:
- `YOUR_ACTUAL_BITMART_API_KEY` → BitMart API Key
- `YOUR_ACTUAL_BITMART_API_SECRET` → BitMart Secret Key
- `YOUR_ACTUAL_BITMART_MEMO` → BitMart Memo (if required)

---

## Step 3: Verify Connector Added

```bash
# Should now show connector
curl https://trading-bridge-production.up.railway.app/clients/70ab29b1-66ad-4645-aec8-fa2f55abe144 | python3 -m json.tool
```

**Expected**:
```json
{
  "connectors": [
    {
      "id": "...",
      "name": "bitmart",
      "api_key": "...",
      "api_secret": "...",
      "memo": "..."
    }
  ]
}
```

---

## Step 4: Test Dashboard

```bash
curl https://trading-bridge-production.up.railway.app/api/exchange/dashboard/client_sharp | python3 -m json.tool
```

**Expected**: Should now return real balances, trades, P&L:
```json
{
  "balance": {
    "total_usdt": 500.0,
    "balances": [
      {"exchange": "bitmart", "asset": "USDT", "total": 500.0, ...},
      {"exchange": "bitmart", "asset": "SHARP", "total": 1000.0, ...}
    ]
  },
  "pnl": {"total": 150.50, ...},
  "volume": {"traded": 10000.0, "trade_count": 25},
  "recent_trades": [...]
}
```

---

## Going Forward: Admin Workflow

When admin creates a client, they MUST:

1. ✅ **Add wallet** (already working)
2. ✅ **Create bot** (already working)
3. ❌ **Add connector with API keys** ← **THIS WAS MISSING**

### Fix Needed

**Option A: Update Admin UI**
- When creating client, include "Add Exchange Connector" step
- Or add prominent reminder: "Don't forget to add API keys!"

**Option B: Auto-Sync from Hummingbot**
- When bot is created, auto-sync connectors from Hummingbot credentials profile
- Requires Hummingbot API endpoint to read credentials

**Option C: Document Workflow**
- Add to admin documentation: "After creating client, add exchange connectors via API Keys tab"

---

## Files to Update

### Admin UI (`ai-trading-ui/src/pages/AdminDashboard.jsx`)
- Add reminder/checklist when creating client
- Or auto-prompt: "Add exchange API keys now?"

### Documentation
- Update client creation workflow docs
- Add connector management guide

---

## Summary

**Immediate Action**: Add BitMart connector via API call above  
**Future Fix**: Update admin workflow to include connector step  
**Long-term**: Consider auto-sync from Hummingbot
