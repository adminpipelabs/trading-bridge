# Verify Trades Are Executing - Complete Check

**Date:** February 10, 2026  
**Time:** 30+ minutes since bot started  
**Expected:** 1-2 trades should be logged (15-25 min intervals)

---

## 🔍 **Step 1: Check Database (Primary Check)**

**Run in Railway PostgreSQL → Query:**

```sql
SELECT 
    b.id as bot_id,
    b.name as bot_name,
    b.status as bot_status,
    b.health_status,
    COUNT(tl.id) as trade_count,
    COALESCE(SUM(tl.cost_usd), 0) as total_volume_usd,
    MAX(tl.created_at) as last_trade_time,
    CASE 
        WHEN MAX(tl.created_at) IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (NOW() - MAX(tl.created_at)))/60
        ELSE NULL
    END as minutes_since_last_trade
FROM bots b
LEFT JOIN trade_logs tl ON tl.bot_id = b.id
WHERE b.name LIKE '%Volume Bot%Coinstore%'
GROUP BY b.id, b.name, b.status, b.health_status
ORDER BY b.updated_at DESC
LIMIT 1;
```

### **Expected Results:**

**✅ If Working:**
- `trade_count >= 1` (should have 1-2 trades after 30 min)
- `total_volume_usd >= 10` (min trade size)
- `last_trade_time` within last 30 minutes

**❌ If Not Working:**
- `trade_count = 0` → **Proceed to Step 2**

---

## 🔍 **Step 2: Check Exchange Order History (Sanity Check)**

**If `trade_count = 0`, check Coinstore directly:**

1. **Login to Coinstore**
2. **Go to:** Order History / Trade History
3. **Filter:** Last 1 hour
4. **Check:** Are there any orders placed?

### **Possible Scenarios:**

#### **Scenario A: Orders Exist on Coinstore BUT `trade_count = 0`**
**Diagnosis:** ✅ Bot IS trading, but ❌ logging is broken

**What to check:**
- `app/cex_bot_runner.py` lines 424-432 (trade logging code)
- Check Hetzner logs for: `"INSERT INTO trade_logs"` errors
- Verify `trade_logs` table exists
- Check for SQL errors in logs

**Fix:** Trade logging bug - trades executing but not being saved

#### **Scenario B: No Orders on Coinstore AND `trade_count = 0`**
**Diagnosis:** ❌ Bot is NOT actually trading

**What to check:**
- Hetzner logs: `journalctl -u trading-bridge -f | grep "market order"`
- Bot runner activity: `grep "CEX Bot Runner\|run_cycle"`
- Exchange API connection errors
- Bot status: Is it actually running?
- Health status: Is there an error message?

**Fix:** Bot execution issue - need to debug why trades aren't executing

---

## 🔍 **Step 3: Check Hetzner Logs**

**SSH to Hetzner:**
```bash
ssh root@5.161.64.209
```

**Check for trade execution:**
```bash
journalctl -u trading-bridge -f --since "30 minutes ago" | grep -i "market order\|trade\|volume"
```

**Look for:**
- ✅ `"Placing BUY market order: ..."`
- ✅ `"✅ BUY market order filled: ..."`
- ✅ `"Bot {id} trade: buy $X.XX"`
- ✅ `"INSERT INTO trade_logs"` (confirms logging attempt)
- ❌ Errors related to trade execution
- ❌ Errors related to database insert

**Check bot runner activity:**
```bash
journalctl -u trading-bridge -f --since "30 minutes ago" | grep -i "CEX Bot Runner\|run_cycle\|Found.*CEX bots"
```

**Look for:**
- `"CEX Bot Runner started"`
- `"Found X CEX bots"`
- `"Bot {id} - Checking if should trade"`
- `"Bot {id} - Interval elapsed, executing trade"`

---

## 📊 **Decision Tree**

```
Query Result: trade_count = 0
    │
    ├─→ Check Coinstore Order History
    │       │
    │       ├─→ Orders EXIST on Coinstore
    │       │       │
    │       │       └─→ ✅ Bot IS trading
    │       │           ❌ Logging is broken
    │       │           → Check: app/cex_bot_runner.py:424-432
    │       │           → Check: trade_logs table exists?
    │       │           → Check: SQL insert errors in logs
    │       │
    │       └─→ No orders on Coinstore
    │               │
    │               └─→ ❌ Bot NOT trading
    │                   → Check: Hetzner logs for execution
    │                   → Check: Bot runner activity
    │                   → Check: Exchange API errors
    │                   → Check: Bot status/health
    │
    └─→ Query Result: trade_count >= 1
            │
            └─→ ✅ Everything working correctly
                → Trades executing and logging
                → Data available for reporting/AI
```

---

## 🔧 **Troubleshooting by Scenario**

### **If Orders Exist on Coinstore but trade_logs Empty:**

**Check 1: Verify trade_logs table exists**
```sql
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'trade_logs'
) as table_exists;
```

**Check 2: Look for insert errors in Hetzner logs**
```bash
journalctl -u trading-bridge -f | grep -i "INSERT INTO trade_logs\|trade_logs.*error\|could not log trade"
```

**Check 3: Verify logging code is being called**
- Check `app/cex_bot_runner.py` line 403: `result = await bot.run_single_cycle()`
- Check line 405: `if result:` (trade executed successfully)
- Check line 424-432: INSERT INTO trade_logs

**Fix:** If table doesn't exist, run migration. If insert failing, check error logs.

---

### **If No Orders on Coinstore:**

**Check 1: Verify bot is actually running**
```sql
SELECT id, name, status, health_status, health_message
FROM bots
WHERE name LIKE '%Volume Bot%Coinstore%';
```

**Check 2: Check bot runner is active**
```bash
# On Hetzner
journalctl -u trading-bridge -f | grep "CEX Bot Runner"
```

**Check 3: Verify exchange connection**
```bash
# Look for initialization errors
journalctl -u trading-bridge -f | grep -i "coinstore\|exchange.*init\|api.*error"
```

**Check 4: Check if bot is waiting for interval**
- Bot may still be within random interval window
- Check `last_trade_time` in bots table
- If NULL, bot hasn't executed first trade yet

**Fix:** Debug why trades aren't executing - check exchange API, bot runner, bot status

---

## ✅ **Quick Verification Checklist**

- [ ] Run SQL query → Check `trade_count`
- [ ] If `trade_count = 0` → Check Coinstore order history
- [ ] Compare: Orders on Coinstore vs `trade_logs` table
- [ ] Check Hetzner logs for trade execution
- [ ] Check Hetzner logs for logging errors
- [ ] Verify `trade_logs` table exists
- [ ] Check bot runner activity
- [ ] Check bot health status

---

## 📋 **Summary**

**Key Question:** After 30 mins with 15-25 min intervals, should have 1-2 trades logged.

**If `trade_count = 0`:**
1. **Check Coinstore Order History** → See if orders exist on exchange
2. **Compare Results:**
   - Orders exist but `trade_logs` empty → **Logging bug**
   - No orders on Coinstore → **Bot not trading**

**Next Steps:**
- Run SQL query to get `trade_count`
- Check Coinstore order history
- Compare results to determine issue
- Follow troubleshooting steps above

---

**Files:**
- `TRADE_CHECK_SUMMARY_FOR_DEV.md` - Complete summary with SQL query
- `CHECK_TRADES_NOW.sql` - Ready-to-run queries
- `VERIFY_TRADES_EXECUTING.md` - This file (complete verification guide)
