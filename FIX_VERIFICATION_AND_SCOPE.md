# Fix Verification & Scope

**Fix Applied:** Bot runner now correctly finds and loads Coinstore bots  
**Date:** February 10, 2026

---

## 🔍 **How to Verify**

### **1. Check Hetzner Logs (Immediate)**

**SSH to Hetzner:**
```bash
ssh root@5.161.64.209
journalctl -u trading-bridge -f | grep -i "coinstore\|Found.*CEX bots\|exchange_credentials"
```

**Look for:**
- ✅ `"Found X CEX bots from main query"` → Bot is being found
- ✅ `"🔍 Bot {id} - Coinstore bot, checking exchange_credentials table..."` → Credentials check
- ✅ `"✅ Found API keys in exchange_credentials table for coinstore"` → Credentials loaded
- ✅ `"✅ Initialized CEX bot: {id}"` → Bot initialized successfully
- ✅ `"Bot {id} trade: buy $X.XX"` → Trades executing

**If you see:**
- ❌ `"⚠️ No credentials found in exchange_credentials table"` → Credentials missing
- ❌ `"❌ Failed to initialize CEX bot"` → Initialization failed

### **2. Check Database (After 15-25 min)**

**Run in Railway PostgreSQL:**
```sql
SELECT 
    b.id,
    b.name,
    b.status,
    b.health_status,
    COUNT(tl.id) as trade_count,
    MAX(tl.created_at) as last_trade
FROM bots b
LEFT JOIN trade_logs tl ON tl.bot_id = b.id
WHERE b.name LIKE '%Volume Bot%Coinstore%'
GROUP BY b.id, b.name, b.status, b.health_status;
```

**Expected:**
- ✅ `trade_count >= 1` after 15-25 minutes
- ✅ `health_status = 'healthy'`
- ✅ `last_trade` shows recent timestamp

### **3. Check UI**

- Bot status shows "Running"
- Volume shows > $0 after trades execute
- Health status shows "healthy"

---

## 📋 **Fix Scope**

### **Type: Permanent Code Fix**

**Not a one-time fix** - This is a code change that runs **every cycle** (every 10 seconds)

**Location:** `app/cex_bot_runner.py`
- Lines 73-85: Query changed from INNER JOIN to LEFT JOIN
- Lines 203-206: Always checks `exchange_credentials` for Coinstore bots

**When it runs:** Every 10 seconds (bot runner cycle)

---

### **Per Exchange Type (Not Per Client)**

**Applies to:** All Coinstore bots for all clients

**Exchange-Specific Logic:**
- **Coinstore:** Always uses `exchange_credentials` table (encrypted)
- **BitMart:** Uses `connectors` table (plaintext) OR `exchange_credentials` as fallback
- **Other exchanges:** Uses `connectors` table primarily, `exchange_credentials` as fallback

**Code Logic:**
```python
# Line 206: For Coinstore, ALWAYS check exchange_credentials
if expected_exchange == "coinstore" or (not api_key or not api_secret):
    # Check exchange_credentials table
```

---

### **Per Client**

**Each client has their own:**
- `exchange_credentials` entry (per exchange)
- Bot instances
- Trade logs

**But:** The fix applies to **all clients** using Coinstore bots

---

## 🔄 **How It Works**

### **Before Fix:**
1. Query used INNER JOIN on `connectors` table
2. Coinstore bots without connectors → **Not found**
3. Bot runner skipped Coinstore bots
4. No trades executed

### **After Fix:**
1. Query uses LEFT JOIN → Finds bots even without connectors
2. For Coinstore bots → Always checks `exchange_credentials` table
3. Loads encrypted credentials
4. Initializes bot successfully
5. Executes trades

---

## ✅ **Verification Checklist**

- [ ] Bot appears in logs: `"Found X CEX bots"`
- [ ] Credentials loaded: `"✅ Found API keys in exchange_credentials table"`
- [ ] Bot initialized: `"✅ Initialized CEX bot"`
- [ ] Trades executing: `"Bot {id} trade: buy $X.XX"`
- [ ] Database shows trades: `trade_count > 0`
- [ ] UI shows volume: `Volume > $0`

---

## 🎯 **Summary**

**Fix Type:** Permanent code change (runs every cycle)  
**Scope:** All Coinstore bots for all clients  
**Exchange-Specific:** Yes (Coinstore only)  
**Per Client:** No (applies to all clients using Coinstore)  

**Verification:**
1. Check Hetzner logs immediately
2. Check database after 15-25 min
3. Check UI for volume

**This fix ensures Coinstore bots are found and initialized correctly for all clients going forward.**
