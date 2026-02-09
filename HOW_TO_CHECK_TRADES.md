# How to Check Bot Trades - Simple Guide

## ✅ **Easiest: Use API in Browser**

### Step 1: Get Bot ID

**Go to Railway Dashboard:**
1. Railway → PostgreSQL → Query Tab
2. Run this SQL:

```sql
SELECT id, name, status, exchange
FROM bots
WHERE account = 'client_new_sharp_foundation'
AND bot_type = 'volume';
```

**Copy the `id` value** (looks like: `7e5f4ad5-c4e0-4d6c-9694-42a337cdb88e`)

---

### Step 2: Check Trades via API

**Open in your browser:**
```
https://trading-bridge-production.up.railway.app/bots/{bot_id}/trades
```

**Replace `{bot_id}` with the ID from Step 1**

**Example:**
```
https://trading-bridge-production.up.railway.app/bots/7e5f4ad5-c4e0-4d6c-9694-42a337cdb88e/trades
```

---

## 📊 **What You'll See**

### If Bot Has Trades:
```json
{
  "bot_id": "...",
  "bot_name": "Sharp-VB-BitMart-Test",
  "total_trades": 5,
  "total_volume_usd": 150.00,
  "buy_count": 3,
  "sell_count": 2,
  "trades": [
    {
      "side": "buy",
      "amount": 1000.0,
      "price": 0.0015,
      "value_usd": 15.00,
      "order_id": "BM123456",
      "created_at": "2026-02-05T10:30:00Z",
      "source": "trade_logs"
    }
  ]
}
```

### If No Trades Yet:
```json
{
  "total_trades": 0,
  "total_volume_usd": 0,
  "trades": []
}
```

---

## 🔍 **Alternative: Check Database Directly**

**Railway → PostgreSQL → Query Tab:**

```sql
-- Step 1: Find bot ID
SELECT id, name, status 
FROM bots 
WHERE account = 'client_new_sharp_foundation' 
AND bot_type = 'volume';

-- Step 2: Check trades (replace {bot_id} with ID from above)
SELECT 
    side,
    amount,
    price,
    cost_usd,
    order_id,
    created_at
FROM trade_logs
WHERE bot_id = '{bot_id}'
ORDER BY created_at DESC
LIMIT 20;

-- Step 3: Count total trades
SELECT 
    COUNT(*) as total_trades,
    SUM(cost_usd) as total_volume,
    COUNT(CASE WHEN side = 'buy' THEN 1 END) as buy_count,
    COUNT(CASE WHEN side = 'sell' THEN 1 END) as sell_count
FROM trade_logs
WHERE bot_id = '{bot_id}';
```

---

## 📋 **Quick Summary**

**To check trades, you need:**

1. **Bot ID** - Get from database query above
2. **API Endpoint** - `GET /bots/{bot_id}/trades`
3. **Or Database** - Query `trade_logs` table directly

**Results show:**
- ✅ Number of trades
- ✅ Total volume in USD
- ✅ Buy vs Sell count
- ✅ Individual trade details
- ✅ Order IDs from BitMart

---

## 🚨 **If No Trades Found**

**Check:**
1. Bot status = "running"?
2. Bot has balance? (check BitMart account)
3. Bot started recently? (trades happen every 15-45 min)
4. Railway logs for errors?

**Check logs:**
- Railway → trading-bridge → Logs tab
- Look for: `Bot {bot_id} trade: ...` or error messages
