# How to Check if Sharp's Bot Has Executed Trades

## Method 1: Check Railway Logs (Easiest)

**In Railway Dashboard:**
1. Go to your `trading-bridge` service
2. Click on **Logs** tab
3. Look for these messages:

**✅ If trades executed:**
```
Bot {bot_id} trade: buy $15.23
Bot {bot_id} trade: sell $18.45
Trade executed: buy $15.23 | Daily: $33.68/$25000
```

**❌ If no trades yet:**
```
Trade skipped — check balance
Health status: stale
```

**⏳ If waiting for interval:**
```
Bot {bot_id} - Checking daily target...
Found 1 wallet(s)
Using wallet: ...
```

---

## Method 2: Check Database (Direct Query)

**In Railway PostgreSQL Query Tab:**

```sql
-- Find Sharp's bot ID
SELECT id, name, status, last_trade_time, health_message
FROM bots
WHERE name LIKE '%BitMart%' OR name LIKE '%Sharp%'
ORDER BY created_at DESC
LIMIT 5;
```

**Then check trades:**
```sql
-- Replace {bot_id} with actual ID from above
SELECT side, amount, price, cost_usd, order_id, created_at
FROM trade_logs
WHERE bot_id = '{bot_id}'
ORDER BY created_at DESC
LIMIT 10;
```

---

## Method 3: Check API Endpoint

**Get bot stats (includes trades):**

```bash
# First, get bot ID from list
curl https://trading-bridge-production.up.railway.app/bots

# Then get stats (replace {bot_id})
curl https://trading-bridge-production.up.railway.app/bots/{bot_id}/stats
```

**Expected response:**
```json
{
  "bot_id": "...",
  "stats": {
    "volume_today": 33.68,
    "trades_today": 2
  },
  "recent_trades": [
    {
      "side": "buy",
      "value_usd": 15.23,
      "created_at": "2026-02-07T20:45:00Z"
    }
  ],
  "total_trades": 2
}
```

---

## What to Look For

### ✅ **Trades Are Executing:**
- `last_trade_time` is recent (within last hour)
- `trade_logs` table has entries
- Railway logs show "Bot {id} trade: ..."
- `health_message` shows "Trade executed: ..."

### ⏳ **Bot Is Running But Waiting:**
- `status` = "running"
- `last_trade_time` = NULL or old
- `health_message` = "Trade skipped — check balance" or similar
- Railway logs show bot checking but not trading

### ❌ **Bot Has Issues:**
- `status` = "error"
- `health_message` contains error details
- Railway logs show errors

---

## Quick Check Commands

**Check if bot is running:**
```bash
curl -s https://trading-bridge-production.up.railway.app/bots | \
  jq '.bots[] | select(.name | contains("BitMart")) | {id, name, status, last_trade_time}'
```

**Check trade count:**
```bash
# After getting bot_id
curl -s https://trading-bridge-production.up.railway.app/bots/{bot_id}/stats | \
  jq '{total_trades, recent_trades: .recent_trades | length}'
```
