# Volume Bot - 15 Minute Check ✅

**Time:** ~15 minutes since bot started  
**Expected:** Bot should have executed at least 1 trade (min interval: 15 min)

---

## ✅ **Quick Verification Steps**

### 1. **Check UI Volume Display**
- Go to bot dashboard
- Check if "Volume" shows > $0
- If still $0, check below

### 2. **Check Hetzner Logs** (Most Reliable)

SSH to Hetzner and check logs:
```bash
ssh root@5.161.64.209
journalctl -u trading-bridge -f --since "15 minutes ago" | grep -i "market order\|trade\|volume"
```

**Look for:**
- `"Placing BUY market order: ..."`
- `"✅ BUY market order filled: ..."`
- `"Trade executed: buy $X.XX"`
- `"Daily volume: $X.XX / $5000"`

### 3. **Check Database Trade Logs**

Query Railway PostgreSQL:
```sql
-- Find bot ID
SELECT id, name, status, health_status, last_trade_time
FROM bots
WHERE name LIKE '%Volume Bot%Coinstore%';

-- Check trades (replace {bot_id})
SELECT side, amount, price, cost_usd, created_at
FROM trade_logs
WHERE bot_id = '{bot_id}'
ORDER BY created_at DESC
LIMIT 10;
```

### 4. **Check Bot Health Status**

```sql
SELECT 
    id,
    name,
    status,
    health_status,
    health_message,
    last_trade_time,
    updated_at
FROM bots
WHERE name LIKE '%Volume Bot%Coinstore%';
```

---

## 🔍 **What to Look For**

### ✅ **Bot is Trading:**
- `trade_logs` table has entries
- `last_trade_time` is recent (< 20 min ago)
- `health_status = 'healthy'`
- Hetzner logs show "market order filled"

### ⏳ **Bot is Waiting:**
- `status = 'running'`
- `last_trade_time = NULL` or old
- `health_status = 'stale'` or NULL
- No errors in logs
- **This is OK** - bot waits random interval (15-25 min)

### ❌ **Bot Has Issues:**
- `health_status = 'error'`
- `health_message` shows error
- Hetzner logs show errors
- Exchange API errors

---

## 📊 **Expected Behavior**

**With current config:**
- Min Interval: 900 seconds (15 min)
- Max Interval: 1500 seconds (25 min)
- Trade Size: 10-15 USD

**First trade should happen:**
- Between 15-25 minutes after bot starts
- Random interval chosen each cycle

**If no trade after 25 minutes:**
- Check logs for errors
- Verify bot runner is active
- Check exchange connection

---

## 🎯 **Next Steps**

1. **If trades found:** ✅ Bot is working correctly
2. **If no trades but bot is running:** Wait up to 25 min (max interval)
3. **If no trades after 25 min:** Check logs for errors
4. **If errors found:** Check exchange API connection, IP whitelist, API keys

---

**Current Status:** Checking if trades executed...
