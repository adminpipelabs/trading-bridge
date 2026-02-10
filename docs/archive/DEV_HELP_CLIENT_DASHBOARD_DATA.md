# Dev Help Request: Client Dashboard Shows $0.00

## Problem Summary

**Client logged in ✅ and sees bot ✅ but all data shows $0.00:**
- Balance: **$0.00**
- P&L: **$0.00** 
- Volume: **$0.00**
- Trades: **None**

The bot IS trading on BitMart. The data EXISTS. But client dashboard doesn't display it.

---

## What We've Implemented

### 1. **Created Client Data Endpoints** (`app/api/client_data.py`)

New endpoints that:
- Look up client by `wallet_address`
- Auto-sync connectors from PostgreSQL → `exchange_manager` (in-memory)
- Query exchanges directly using `ccxt` via `exchange_manager`

**Endpoints**:
- `GET /api/clients/portfolio?wallet_address=0x...` - Portfolio balances + bot counts
- `GET /api/clients/balances?wallet_address=0x...` - Balances array
- `GET /api/clients/trades?wallet_address=0x...&trading_pair=SHARP-USDT&limit=100&days=7` - Trade history
- `GET /api/clients/volume?wallet_address=0x...&days=7` - Trading volume
- `GET /api/clients/pnl?wallet_address=0x...&days=7` - Profit & Loss

### 2. **Auto-Sync Function**

```python
async def sync_connectors_to_exchange_manager(account_identifier: str, db: Session):
    """
    Load connectors from database into exchange_manager for an account.
    This ensures exchange_manager has the API keys needed to query exchanges.
    """
    # 1. Get client from DB
    # 2. Get or create account in exchange_manager
    # 3. Load connectors from DB
    # 4. Add each connector to exchange_manager (if not already loaded)
```

### 3. **Fixed Response Format** (to match frontend expectations)

- **Balances**: Returns array `[{exchange, asset, free, total, usd_value}]`
- **Trades**: Returns array with `{trading_pair, exchange, side, amount, price, timestamp}`
- **Portfolio**: Includes `{total_pnl, active_bots, total_bots}`
- **Volume**: Includes `{total_volume, trade_count}`

---

## Current Status

### ✅ What's Working:
1. Endpoints exist and are deployed
2. Auto-sync function implemented
3. Response format matches frontend expectations
4. Frontend calls endpoints with `wallet_address` parameter

### ❌ What's NOT Working:
1. **Client dashboard still shows $0.00**
2. **No data displayed** (balances, trades, volume all empty)

---

## Key Questions for Dev

### 1. **Where are BitMart API keys stored?**

**Check**:
```bash
curl https://trading-bridge-production.up.railway.app/clients
```

**Expected**: Sharp Foundation should have `connectors` array with:
```json
{
  "connectors": [
    {
      "name": "bitmart",
      "api_key": "...",
      "api_secret": "...",
      "memo": "..."
    }
  ]
}
```

**Question**: Are connectors stored in PostgreSQL `connectors` table? Or only in Hummingbot?

### 2. **Does the sync function work?**

**Check logs** when calling:
```bash
curl "https://trading-bridge-production.up.railway.app/api/clients/balances?wallet_address=0x6cc52d4b397e0ddfdcd1ecbb37902003c4801685"
```

**Expected logs**:
- `✅ Synced connector bitmart to exchange_manager for client_sharp`
- `Making GET request to BitMart API...`
- `Balance data returned`

**Question**: Are connectors being loaded from DB → `exchange_manager`? Check Railway logs.

### 3. **Can `exchange_manager` query BitMart?**

**Test**:
```bash
# Should return balances from BitMart
curl "https://trading-bridge-production.up.railway.app/api/clients/balances?wallet_address=0x6cc52d4b397e0ddfdcd1ecbb37902003c4801685"
```

**Expected response**:
```json
[
  {
    "exchange": "bitmart",
    "asset": "SHARP",
    "free": 1000.0,
    "total": 1000.0,
    "usd_value": 0
  },
  {
    "exchange": "bitmart",
    "asset": "USDT",
    "free": 500.0,
    "total": 500.0,
    "usd_value": 500.0
  }
]
```

**Question**: Is `ccxt` successfully querying BitMart? Or are there API errors?

### 4. **Frontend API calls - are they working?**

**Check browser console** when client views dashboard:
- Network tab → Look for `/api/clients/balances`, `/api/clients/trades`, etc.
- Check response status (200? 404? 500?)
- Check response body (empty? error? data?)

**Question**: Are frontend API calls succeeding? What errors appear?

### 5. **Which approach should we use?**

**Option A**: Query exchanges directly via `ccxt` (current implementation)
- ✅ Real-time data
- ✅ Works even if Hummingbot is down
- ❌ Needs API keys stored in `trading-bridge` DB

**Option B**: Query Hummingbot API
- ✅ Uses existing Hummingbot connectors
- ❌ Requires Hummingbot to expose balance/trade endpoints
- ❌ Adds dependency on Hummingbot being online

**Option C**: Hummingbot pushes data to `trading-bridge` (webhook)
- ✅ Real-time updates
- ❌ Requires Hummingbot webhook implementation

**Question**: Which approach do you recommend? Or is there a better way?

---

## Debugging Steps Needed

### Step 1: Verify Connectors in Database
```sql
-- Run in Railway PostgreSQL
SELECT c.name, c.account_identifier, conn.name, conn.api_key IS NOT NULL as has_key
FROM clients c
LEFT JOIN connectors conn ON conn.client_id = c.id
WHERE c.account_identifier = 'client_sharp';
```

**Expected**: Should show BitMart connector with `api_key` and `api_secret`.

### Step 2: Test Sync Function
```bash
# Check Railway logs when calling endpoint
curl -v "https://trading-bridge-production.up.railway.app/api/clients/balances?wallet_address=0x6cc52d4b397e0ddfdcd1ecbb37902003c4801685"
```

**Look for**:
- `✅ Synced connector bitmart to exchange_manager`
- `Failed to sync connector` (errors)
- `No connectors found for account`

### Step 3: Test Exchange Query
```python
# Test if ccxt can query BitMart with stored API keys
import ccxt
exchange = ccxt.bitmart({
    'apiKey': '...',
    'secret': '...',
    'uid': '...'  # memo
})
balance = await exchange.fetch_balance()
print(balance)
```

**Expected**: Should return balance data from BitMart.

### Step 4: Check Frontend Network Calls
- Open browser DevTools → Network tab
- Log in as client
- View dashboard
- Check `/api/clients/*` requests:
  - Status code?
  - Response body?
  - Errors?

---

## Files Changed

### Backend:
- ✅ `app/api/client_data.py` (NEW) - Client data endpoints
- ✅ `app/main.py` - Added `client_data.router`
- ✅ `app/database.py` - Already has `Connector` model

### Frontend:
- ✅ `src/services/api.js` - Updated `clientAPI` to pass `wallet_address`

---

## Next Steps Needed

1. **Verify connectors exist in DB** - Check PostgreSQL `connectors` table
2. **Test sync function** - Check Railway logs for sync success/failure
3. **Test exchange query** - Verify `ccxt` can query BitMart with stored keys
4. **Check frontend calls** - Verify API requests are being made correctly
5. **Decide on approach** - Query exchanges directly vs. Hummingbot API vs. webhook

---

## Request for Dev Help

**Please help us debug**:
1. Where are BitMart API keys actually stored? (DB? Hummingbot only?)
2. Is the sync function working? (Check logs)
3. Can `ccxt` query BitMart successfully? (Test with stored keys)
4. Are frontend API calls working? (Check browser network tab)
5. Which approach should we use? (Direct query vs. Hummingbot API)

**Full details in**: `CLIENT_DASHBOARD_DATA_SOLUTION.md` and `CLIENT_DASHBOARD_RESPONSE_FORMAT_MISMATCH.md`
