# Client Dashboard Response Format Mismatch

## Problem

Backend endpoints return data in a different format than the frontend expects. The frontend displays $0.00 because it can't parse the backend responses.

---

## Frontend Expectations vs Backend Responses

### 1. **Balances** (`/api/clients/balances`)

**Frontend expects** (array):
```javascript
[
  {
    exchange: "bitmart",
    asset: "SHARP",
    free: 1000.0,
    total: 1000.0,
    usd_value: 500.0
  },
  {
    exchange: "bitmart",
    asset: "USDT",
    free: 500.0,
    total: 500.0,
    usd_value: 500.0
  }
]
```

**Backend returns** (nested object):
```json
{
  "balances": {
    "bitmart": {
      "SHARP": {
        "total": 1000.0,
        "free": 1000.0,
        "used": 0.0
      },
      "USDT": {
        "total": 500.0,
        "free": 500.0,
        "used": 0.0
      }
    }
  },
  "total_usd": 0
}
```

**Fix needed**: Transform nested object → flat array with `exchange`, `asset`, `usd_value`

---

### 2. **Portfolio** (`/api/clients/portfolio`)

**Frontend expects**:
```javascript
{
  total_pnl: 150.50,        // Profit & Loss
  active_bots: 2,           // Number of running bots
  total_bots: 3             // Total bots
}
```

**Backend returns**:
```json
{
  "account": "client_sharp",
  "balances": {...},
  "total_usd": 0
}
```

**Fix needed**: Add `total_pnl`, `active_bots`, `total_bots` fields

---

### 3. **Trades** (`/api/clients/trades`)

**Frontend expects** (array):
```javascript
[
  {
    trading_pair: "SHARP-USDT",  // Required
    side: "buy",
    amount: 100.0,
    price: 0.5,
    timestamp: 1234567890,
    exchange: "bitmart"          // Required
  }
]
```

**Backend returns** (array):
```json
[
  {
    "connector": "bitmart",      // Should be "exchange"
    "symbol": "SHARP/USDT",       // Should be "trading_pair" with "-" separator
    "side": "buy",
    "amount": 100.0,
    "price": 0.5,
    "timestamp": 1234567890
  }
]
```

**Fix needed**: 
- Rename `connector` → `exchange`
- Rename `symbol` → `trading_pair`
- Convert `SHARP/USDT` → `SHARP-USDT`

---

### 4. **Volume** (`/api/clients/volume`)

**Frontend expects**:
```javascript
{
  total_volume: 10000.0,    // USD volume
  trade_count: 25           // Number of trades
}
```

**Backend returns**:
```json
{
  "account": "client_sharp",
  "total_volume_usd": 10000.0,
  "volume_by_pair": {...},
  "days": 7
}
```

**Fix needed**: 
- Rename `total_volume_usd` → `total_volume`
- Add `trade_count` field

---

## Solution Options

### Option 1: Transform in Backend (Recommended)
Update `app/api/client_data.py` to transform responses to match frontend format.

**Pros**:
- Frontend doesn't need changes
- Single source of truth (backend)
- Easier to maintain

**Cons**:
- Backend needs transformation logic

### Option 2: Transform in Frontend
Update `src/services/api.js` to transform backend responses.

**Pros**:
- Backend stays simple
- Frontend has control

**Cons**:
- Frontend needs transformation logic
- More complex frontend code

---

## Recommended Fix (Option 1)

Update backend endpoints to return frontend-compatible format:

1. **`/api/clients/balances`**: Flatten nested balances → array
2. **`/api/clients/portfolio`**: Add `total_pnl`, `active_bots`, `total_bots`
3. **`/api/clients/trades`**: Rename fields (`connector`→`exchange`, `symbol`→`trading_pair`)
4. **`/api/clients/volume`**: Rename `total_volume_usd`→`total_volume`, add `trade_count`

---

## Files to Update

- `trading-bridge/app/api/client_data.py` - Transform responses
- May need to query bot status for `active_bots`/`total_bots` in portfolio endpoint

---

## Testing

After fix, test with:
```bash
# Should return array of balances
curl "https://trading-bridge-production.up.railway.app/api/clients/balances?wallet_address=0x6cc52d4b397e0ddfdcd1ecbb37902003c4801685"

# Should return portfolio with total_pnl, active_bots, total_bots
curl "https://trading-bridge-production.up.railway.app/api/clients/portfolio?wallet_address=0x6cc52d4b397e0ddfdcd1ecbb37902003c4801685"
```
