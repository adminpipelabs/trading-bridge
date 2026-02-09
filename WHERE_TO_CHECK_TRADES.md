# Where to Check Bot Trades - Quick Guide

## 🚀 **Easiest Way: Run the Script**

```bash
python3 check_bot_trades_now.py
```

**This will:**
1. ✅ Find Sharp's bot automatically
2. ✅ Check both trade tables
3. ✅ Show all trades with details
4. ✅ Show summary stats

---

## 🌐 **Option 2: Use API Directly**

### Step 1: Find Bot ID

**In Browser:**
```
https://trading-bridge-production.up.railway.app/bots
```

**Or with curl:**
```bash
curl https://trading-bridge-production.up.railway.app/bots | jq '.[] | select(.account == "client_new_sharp_foundation" and .bot_type == "volume")'
```

**Look for:** `"id": "..."` - that's your bot_id

---

### Step 2: Check Trades

**In Browser:**
```
https://trading-bridge-production.up.railway.app/bots/{bot_id}/trades
```

**Or with curl:**
```bash
curl https://trading-bridge-production.up.railway.app/bots/{bot_id}/trades | jq
```

**Replace `{bot_id}` with actual ID from Step 1**

---

### Step 3: Check Stats (includes trades)

**In Browser:**
```
https://trading-bridge-production.up.railway.app/bots/{bot_id}/stats
```

**Or with curl:**
```bash
curl https://trading-bridge-production.up.railway.app/bots/{bot_id}/stats | jq
```

---

## 📊 **What You'll See**

### If Trades Exist:
```json
{
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

### If No Trades:
```json
{
  "total_trades": 0,
  "total_volume_usd": 0,
  "trades": []
}
```

---

## 🔍 **Option 3: Railway Dashboard**

1. Go to: https://railway.app/dashboard
2. Click on **trading-bridge** service
3. Click **Logs** tab
4. Look for:
   - `Bot {bot_id} trade: buy $15.23` ← Trade executed
   - `Bot {bot_id} missing API keys` ← Problem

---

## 🗄️ **Option 4: Database Direct Query**

**Railway → PostgreSQL → Query Tab:**

```sql
-- Find bot ID
SELECT id, name FROM bots 
WHERE account = 'client_new_sharp_foundation' 
AND bot_type = 'volume';

-- Check trades (replace {bot_id})
SELECT side, amount, price, cost_usd, order_id, created_at
FROM trade_logs
WHERE bot_id = '{bot_id}'
ORDER BY created_at DESC;
```

---

## ✅ **Recommended: Use the Script**

**Just run:**
```bash
python3 check_bot_trades_now.py
```

**It does everything automatically!**
