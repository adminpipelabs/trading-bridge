# Check Volume Bot Trades on BitMart

## Quick Check Methods

### Method 1: Run Python Script (Local)

```bash
# Set DATABASE_URL from Railway
export DATABASE_URL='postgresql://postgres:...@...railway.app:5432/railway'

# Run script
python3 check_volume_bot_trades.py
```

**This will show:**
- ✅ Bot found
- ✅ Number of trades executed
- ✅ Trade details (side, amount, price, cost)
- ✅ Total volume
- ❌ If no trades: possible reasons

---

### Method 2: Check Railway Logs

**Look for these log messages:**

```
Bot {bot_id} trade: buy $15.23
Bot {bot_id} trade: sell $20.45
```

**Or errors:**
```
❌ Bot {bot_id} missing API keys
❌ Failed to initialize exchange
❌ Insufficient funds
```

---

### Method 3: Query Database Directly (Railway PostgreSQL)

**Go to Railway → PostgreSQL → Query tab:**

```sql
-- Find Sharp's bot
SELECT id, name, status, exchange, created_at
FROM bots
WHERE account = 'client_new_sharp_foundation'
AND bot_type = 'volume'
AND (exchange = 'bitmart' OR name ILIKE '%bitmart%');

-- Check trades (replace {bot_id} with actual ID from above)
SELECT id, side, amount, price, cost_usd, order_id, created_at
FROM trade_logs
WHERE bot_id = '{bot_id}'
ORDER BY created_at DESC
LIMIT 20;

-- Count total trades
SELECT COUNT(*) as total_trades, SUM(cost_usd) as total_volume
FROM trade_logs
WHERE bot_id = '{bot_id}';
```

---

### Method 4: Check Bot Health Status

```sql
SELECT 
    id,
    name,
    status,
    health_status,
    health_message,
    last_trade_time,
    status_updated_at
FROM bots
WHERE account = 'client_new_sharp_foundation'
AND bot_type = 'volume';
```

**Look for:**
- `health_status = 'healthy'` → Bot is working
- `health_status = 'stale'` → No recent trades
- `health_status = 'error'` → Bot has errors
- `last_trade_time` → When last trade happened

---

## What to Expect

### ✅ **If Bot is Trading:**

```
✅ Found 5 trade(s) in trade_logs table:

  📊 Trade #1
     Side: BUY
     Amount: 1000.0 SHARP
     Price: $0.0015
     Cost: $15.00
     Order ID: BM1234567890
     Time: 2026-02-05 10:30:00

💰 Total Volume: $150.00
```

### ❌ **If Bot is NOT Trading:**

```
❌ No trades found in trade_logs table

Possible reasons:
  1. Bot just started (trades happen every 15-45 minutes)
  2. Bot doesn't have enough balance
  3. Bot is not running (check status)
  4. API keys are invalid
  5. Exchange API errors
```

---

## Troubleshooting

### Bot Status = "running" but No Trades

**Check:**
1. **Balance** - Does bot have USDT or SHARP?
   ```sql
   -- Check via BitMart API (need to query exchange)
   ```

2. **API Keys** - Are they valid?
   ```sql
   SELECT exchange, created_at
   FROM exchange_credentials
   WHERE client_id = (SELECT id FROM clients WHERE account_identifier = 'client_new_sharp_foundation');
   ```

3. **Bot Config** - Are intervals reasonable?
   ```sql
   SELECT config
   FROM bots
   WHERE account = 'client_new_sharp_foundation'
   AND bot_type = 'volume';
   ```
   Should show: `interval_min_seconds: 900` (15 min), `interval_max_seconds: 2700` (45 min)

4. **Railway Logs** - Check for errors:
   - "Failed to initialize exchange"
   - "Insufficient funds"
   - "Missing API keys"

---

## Expected Trade Frequency

**Volume bot trades every:**
- Minimum: 15 minutes (`interval_min_seconds: 900`)
- Maximum: 45 minutes (`interval_max_seconds: 2700`)
- Random interval between min/max

**So if bot started 10 minutes ago:**
- ❌ Too early - wait 5 more minutes

**If bot started 1 hour ago:**
- ✅ Should have at least 1-2 trades by now
- ❌ If zero trades = problem

---

## Next Steps

1. **Run the check script** → See if trades exist
2. **If no trades** → Check Railway logs for errors
3. **If errors** → Fix API keys, balance, or bot config
4. **If still no trades** → Check BitMart account directly for balance
