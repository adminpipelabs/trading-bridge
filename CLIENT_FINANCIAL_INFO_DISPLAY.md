# What Financial Information Clients See

## ✅ Current Implementation

### Endpoint: `GET /bots/{bot_id}/balance-and-volume`

**Returns:**
```json
{
  "bot_id": "...",
  "bot_type": "volume",
  "pair": "SHARP/USDT",
  "available": {
    "SHARP": 0,
    "USDT": 0
  },
  "locked": {
    "SHARP": 0,
    "USDT": 0
  },
  "volume": {
    "type": "volume_traded",
    "value_usd": 0,
    "total_volume_usd": 0,
    "total_trades": 0
  }
}
```

---

## 📊 What Clients Should See

### 1. **Available Funds** ✅
- **What:** Funds available for trading (not in orders)
- **Source:** `available` object from endpoint
- **Display:** "Available: 8,000,000 SHARP | 1,500 USDT"

### 2. **Locked Funds** ✅
- **What:** Funds locked in open orders
- **Source:** `locked` object from endpoint
- **Display:** "Locked: 0 SHARP | 0 USDT"

### 3. **Volume** ✅
- **What:** Total trading volume (USD)
- **Source:** `volume.value_usd` from endpoint
- **Display:** "Volume: $5,234.50"

### 4. **P&L** ❌ **MISSING**
- **What:** Profit & Loss from trading
- **Source:** Need to calculate from trades
- **Display:** "P&L: +$123.45" or "P&L: -$45.67"

---

## 🚨 Problem: P&L Not Included

**Current Status:**
- ✅ Available Funds - Included
- ✅ Locked Funds - Included
- ✅ Volume - Included
- ❌ **P&L - NOT included in bot endpoint**

**Solution:** Add P&L calculation to `/bots/{bot_id}/balance-and-volume` endpoint

---

## ✅ Fix: Add P&L to Bot Endpoint

**File:** `app/bot_routes.py`

**Add P&L calculation to `get_bot_balance_and_volume`:**

```python
# After volume calculation, add P&L
# Calculate P&L from trades
try:
    # Get trades for this bot
    bot_trades = db.execute(text("""
        SELECT side, amount, price, cost_usd, created_at
        FROM trade_logs
        WHERE bot_id = :bot_id
        ORDER BY created_at ASC
    """), {"bot_id": bot_id}).fetchall()
    
    # Calculate P&L using FIFO method
    positions = []  # List of (amount, avg_price)
    total_pnl = 0.0
    
    for trade in bot_trades:
        side = trade.side.lower()
        amount = float(trade.amount or 0)
        price = float(trade.price or 0)
        
        if side == "buy":
            # Add to position
            positions.append((amount, price))
        elif side == "sell":
            # Realize P&L
            remaining_sell = amount
            while remaining_sell > 0 and positions:
                buy_amount, buy_price = positions.pop(0)
                sell_amount = min(remaining_sell, buy_amount)
                pnl = (price - buy_price) * sell_amount
                total_pnl += pnl
                remaining_sell -= sell_amount
                if buy_amount > sell_amount:
                    # Put remaining back
                    positions.insert(0, (buy_amount - sell_amount, buy_price))
    
    result["pnl"] = {
        "total_usd": round(total_pnl, 2),
        "unrealized_usd": 0,  # TODO: Calculate from current positions
        "trade_count": len(bot_trades)
    }
except Exception as e:
    logger.warning(f"Failed to calculate P&L for bot {bot_id}: {e}")
    result["pnl"] = {
        "total_usd": 0,
        "unrealized_usd": 0,
        "trade_count": 0
    }
```

---

## 📋 Complete Response Format

**After fix, endpoint returns:**

```json
{
  "bot_id": "...",
  "bot_type": "volume",
  "pair": "SHARP/USDT",
  "available": {
    "SHARP": 8000000,
    "USDT": 1500
  },
  "locked": {
    "SHARP": 0,
    "USDT": 0
  },
  "volume": {
    "type": "volume_traded",
    "value_usd": 5234.50,
    "total_volume_usd": 5234.50,
    "total_trades": 45
  },
  "pnl": {
    "total_usd": 123.45,
    "unrealized_usd": 0,
    "trade_count": 45
  }
}
```

---

## 🎨 Frontend Display

**What clients see in bot card:**

```
┌─────────────────────────────────────┐
│ SHARP-VB-BitMart          [Running] │
├─────────────────────────────────────┤
│ Available Funds                     │
│ 8,000,000 SHARP | 1,500 USDT        │
│                                     │
│ Locked Funds                        │
│ 0 SHARP | 0 USDT                    │
│                                     │
│ Volume                              │
│ $5,234.50                           │
│                                     │
│ P&L                                 │
│ +$123.45                            │
└─────────────────────────────────────┘
```

---

## ✅ Summary

**Current:**
- ✅ Available Funds - Working
- ✅ Locked Funds - Working
- ✅ Volume - Working
- ❌ P&L - Missing

**After Fix:**
- ✅ Available Funds - Working
- ✅ Locked Funds - Working
- ✅ Volume - Working
- ✅ P&L - Added

**Action:** Add P&L calculation to `/bots/{bot_id}/balance-and-volume` endpoint.
