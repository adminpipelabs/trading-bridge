# How to Check if Trades Are Being Logged - RIGHT NOW

**Time:** 30+ minutes since bot started  
**Expected:** Bot should have executed at least 1 trade

---

## 🚀 **Quick Check (Railway PostgreSQL)**

### **Option 1: Run Combined Query (Easiest)**

Go to **Railway → PostgreSQL → Query** and run:

```sql
SELECT 
    b.id as bot_id,
    b.name as bot_name,
    b.status as bot_status,
    b.health_status,
    b.last_trade_time,
    COUNT(tl.id) as trade_count,
    COALESCE(SUM(tl.cost_usd), 0) as total_volume_usd,
    MAX(tl.created_at) as last_trade_time_from_logs,
    CASE 
        WHEN MAX(tl.created_at) IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (NOW() - MAX(tl.created_at)))/60
        ELSE NULL
    END as minutes_since_last_trade
FROM bots b
LEFT JOIN trade_logs tl ON tl.bot_id = b.id
WHERE b.name LIKE '%Volume Bot%Coinstore%'
GROUP BY b.id, b.name, b.status, b.health_status, b.last_trade_time
ORDER BY b.updated_at DESC
LIMIT 1;
```

**What to look for:**
- ✅ `trade_count > 0` → Trades are being logged!
- ✅ `total_volume_usd > 0` → Volume is accumulating
- ✅ `last_trade_time_from_logs` → Shows when last trade happened
- ❌ `trade_count = 0` → No trades logged yet

---

### **Option 2: Check Recent Trades**

```sql
-- First get bot_id from above query, then:
SELECT 
    side,
    amount,
    price,
    cost_usd,
    order_id,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_ago
FROM trade_logs
WHERE bot_id = '{bot_id_from_above}'
ORDER BY created_at DESC
LIMIT 10;
```

---

## 🔍 **If No Trades Found**

### **Check 1: Verify trade_logs Table Exists**

```sql
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'trade_logs'
) as table_exists;
```

**If `table_exists = false`:**
- Run migration: `migrations/add_cex_volume_bot.sql`

### **Check 2: Verify Bot Status**

```sql
SELECT id, name, status, health_status, health_message, last_trade_time
FROM bots
WHERE name LIKE '%Volume Bot%Coinstore%';
```

**Look for:**
- `status = 'running'` → Bot should be active
- `health_status = 'healthy'` → Bot is working
- `health_status = 'stale'` → Bot waiting or not trading
- `health_status = 'error'` → Bot has errors

### **Check 3: Check Hetzner Logs**

```bash
ssh root@5.161.64.209
journalctl -u trading-bridge -f --since "30 minutes ago" | grep -i "market order\|trade\|volume"
```

**Look for:**
- `"Placing BUY market order: ..."`
- `"✅ BUY market order filled: ..."`
- `"Bot {id} trade: buy $X.XX"`
- `"INSERT INTO trade_logs"`

---

## 📊 **Expected Results After 30 Minutes**

### ✅ **If Bot is Working:**
- `trade_count >= 1` (at least 1 trade)
- `total_volume_usd >= 10` (min trade size)
- `last_trade_time_from_logs` within last 30 minutes
- `health_status = 'healthy'`

### ⏳ **If Bot is Waiting:**
- `trade_count = 0`
- `status = 'running'`
- `health_status = 'stale'` or NULL
- Bot may still be within random interval (15-25 min)

### ❌ **If Bot Has Issues:**
- `health_status = 'error'`
- `health_message` shows error
- Check Hetzner logs for errors

---

## 🎯 **Next Steps**

1. **Run the SQL query above** → See if trades exist
2. **If trades found:** ✅ Data is being stored correctly
3. **If no trades:** Check Hetzner logs for execution errors
4. **If table missing:** Run migration to create `trade_logs` table

---

**File:** `CHECK_TRADES_NOW.sql` contains all queries ready to run.
