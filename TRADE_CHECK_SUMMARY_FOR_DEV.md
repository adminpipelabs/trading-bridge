# Trade Data Check Summary - For Dev

**Date:** February 10, 2026  
**Time:** ~30+ minutes since Volume Bot started  
**Bot:** SHARP Volume Bot - Coinstore - correct  
**Status:** Running  
**Expected:** Bot should have executed at least 1 trade (min interval: 15 min)

---

## 🔍 **Query to Run**

**Go to Railway → PostgreSQL → Query tab and run:**

```sql
SELECT 
    b.id as bot_id,
    b.name as bot_name,
    b.status as bot_status,
    b.health_status,
    b.health_message,
    b.last_trade_time as bot_last_trade_time,
    COUNT(tl.id) as trade_count,
    COALESCE(SUM(tl.cost_usd), 0) as total_volume_usd,
    COALESCE(SUM(CASE WHEN tl.side = 'buy' THEN tl.cost_usd ELSE 0 END), 0) as buy_volume,
    COALESCE(SUM(CASE WHEN tl.side = 'sell' THEN tl.cost_usd ELSE 0 END), 0) as sell_volume,
    COUNT(CASE WHEN tl.side = 'buy' THEN 1 END) as buy_count,
    COUNT(CASE WHEN tl.side = 'sell' THEN 1 END) as sell_count,
    COALESCE(AVG(tl.cost_usd), 0) as avg_trade_size,
    MAX(tl.created_at) as last_trade_time_from_logs,
    CASE 
        WHEN MAX(tl.created_at) IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (NOW() - MAX(tl.created_at)))/60
        ELSE NULL
    END as minutes_since_last_trade
FROM bots b
LEFT JOIN trade_logs tl ON tl.bot_id = b.id
WHERE b.name LIKE '%Volume Bot%Coinstore%'
GROUP BY b.id, b.name, b.status, b.health_status, b.health_message, b.last_trade_time
ORDER BY b.updated_at DESC
LIMIT 1;
```

---

## 📊 **What to Check**

### **1. Trade Count**
- ✅ `trade_count > 0` → Trades are being logged correctly
- ❌ `trade_count = 0` → No trades logged (see troubleshooting below)

### **2. Total Volume**
- ✅ `total_volume_usd > 0` → Volume is accumulating
- ❌ `total_volume_usd = 0` → No volume generated

### **3. Last Trade Time**
- ✅ `last_trade_time_from_logs` shows recent timestamp → Bot is trading
- ❌ `last_trade_time_from_logs = NULL` → No trades executed

### **4. Health Status**
- ✅ `health_status = 'healthy'` → Bot is working
- ⚠️ `health_status = 'stale'` → Bot waiting or not trading
- ❌ `health_status = 'error'` → Bot has errors

---

## 🔍 **If No Trades Found**

### **Step 1: Verify trade_logs Table Exists**

```sql
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'trade_logs'
) as table_exists;
```

**If `table_exists = false`:**
- Run migration: `migrations/add_cex_volume_bot.sql`
- This creates the `trade_logs` table

### **Step 2: Check Recent Trades (Detailed)**

```sql
-- Get bot_id from first query, then:
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

### **Step 3: Check Hetzner Logs**

**SSH to Hetzner:**
```bash
ssh root@5.161.64.209
journalctl -u trading-bridge -f --since "30 minutes ago" | grep -i "market order\|trade\|volume"
```

**Look for:**
- `"Placing BUY market order: ..."`
- `"✅ BUY market order filled: ..."`
- `"Bot {id} trade: buy $X.XX"`
- `"INSERT INTO trade_logs"` (confirms logging)
- Any errors related to trade execution

### **Step 4: Verify Bot Runner is Active**

**Check if CEX bot runner is running:**
```bash
# On Hetzner
journalctl -u trading-bridge -f | grep -i "CEX Bot Runner\|run_cycle"
```

**Look for:**
- `"CEX Bot Runner started"`
- `"Found X CEX bots"`
- `"Bot {id} trade: ..."`

---

## 📋 **Current Bot Configuration**

**From UI (confirmed):**
- Daily Volume Target: 5000 USD
- Min Trade: 10 USD
- Max Trade: 15 USD
- Min Interval: 900 seconds (15 min)
- Max Interval: 1500 seconds (25 min)
- Slippage Tolerance: 50 bps (0.5%)

**Implementation:**
- ✅ Uses market orders (`create_market_buy_order` / `create_market_sell_order`)
- ✅ Trade logging code: `app/cex_bot_runner.py` lines 424-432
- ✅ Stores to `trade_logs` table with: bot_id, side, amount, price, cost_usd, order_id, created_at

---

## 🎯 **Expected Behavior**

**With current config:**
- Bot should execute first trade between 15-25 minutes after start
- Random interval chosen each cycle
- Each trade should be logged to `trade_logs` table
- Volume should accumulate in `cost_usd` column

**After 30 minutes:**
- ✅ Should have at least 1 trade logged
- ✅ `trade_count >= 1`
- ✅ `total_volume_usd >= 10` (min trade size)

---

## 🔧 **Troubleshooting**

### **If `trade_count = 0`:**

**Possible Causes:**
1. **Bot waiting for interval** - Still within random 15-25 min window
2. **Bot runner not executing** - Check Hetzner logs
3. **Trade execution failing** - Check exchange API errors
4. **trade_logs insert failing** - Check for SQL errors in logs
5. **Table doesn't exist** - Run migration

**Check Logs For:**
- Trade execution attempts
- Market order placement
- Exchange API responses
- Database insert errors
- Bot runner activity

### **If `health_status = 'error'`:**
- Check `health_message` for error details
- Review Hetzner logs for exception tracebacks
- Verify exchange API connection
- Check IP whitelist status

---

## 📊 **Data Storage Location**

**Table:** `trade_logs` in Railway PostgreSQL

**Schema:**
```sql
CREATE TABLE trade_logs (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) NOT NULL,
    side VARCHAR(10) NOT NULL,        -- 'buy' or 'sell'
    amount DECIMAL(20, 8),             -- Trade amount
    price DECIMAL(20, 8),              -- Execution price
    cost_usd DECIMAL(20, 2),           -- Trade value in USD
    order_id VARCHAR(255),             -- Exchange order ID
    created_at TIMESTAMP DEFAULT NOW() -- Trade timestamp
);
```

**Code Location:**
- Trade logging: `app/cex_bot_runner.py` lines 424-432
- Trade execution: `app/cex_volume_bot.py` lines 589-670 (execute_trade method)

---

## 🔌 **API Endpoints for Trade Data**

**Get Trade History:**
```
GET /bots/{bot_id}/trades-history
```

**Get Balance & Volume (includes trades):**
```
GET /bots/{bot_id}/balance-and-volume
```

**Get Paginated Trades:**
```
GET /bots/{bot_id}/trades?limit=50
```

---

## ✅ **Next Steps**

1. **Run the SQL query above** → Check if trades exist
2. **If trades found:** ✅ Data is being stored correctly for reporting/AI
3. **If no trades:** Follow troubleshooting steps above
4. **Check Hetzner logs** → Verify bot is executing trades
5. **Verify trade_logs table exists** → Run migration if needed

---

## 📝 **Summary**

**Current Status:** Bot is running, configuration confirmed  
**Data Storage:** `trade_logs` table (if exists)  
**Trade Logging Code:** `app/cex_bot_runner.py:424-432`  
**Expected:** At least 1 trade after 30 minutes  

**Action Required:** Run SQL query to verify trades are being logged

---

**Files Created:**
- `CHECK_TRADES_NOW.sql` - Ready-to-run SQL queries
- `HOW_TO_CHECK_TRADES_NOW.md` - Detailed verification guide
- `TRADE_DATA_STORAGE_AND_ACCESS.md` - Complete data access documentation
