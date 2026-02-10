# Balance Showing Zero - Issue for Dev

**Date:** February 10, 2026  
**Status:** Bot running but balances show 0

---

## 🎯 **Current Architecture**

### **Backend:**
- **Primary:** Hetzner VPS (`5.161.64.209`)
  - Trading Bridge API running
  - Bots executing here
  - Connects to Railway Postgres database

- **Optional:** Railway (`162.220.232.99`)
  - Can run simultaneously (redundancy)
  - Or stopped to save costs

### **Frontend:**
- **Railway:** `ai-trading-ui` service
  - URL: `https://app.pipelabs.xyz`
  - Auto-deploys from GitHub

### **Database:**
- **Railway Postgres**
  - Both Hetzner and Railway backends use this
  - Contains all bot data, credentials, configs

---

## 🐛 **The Problem**

**Bot Status:** ✅ Running (green badge)  
**Balances:** ❌ All showing 0
- Available: 0 SHARP | 0 USDT
- Locked: 0 SHARP | 0 USDT  
- Volume: $0
- P&L: +$0

**Bot:** SHARP Volume Bot - Coinstore

---

## ✅ **What We Know Works**

1. **Coinstore API Connection:** ✅ Working
   - IP whitelisting complete (`5.161.64.209` and `162.220.232.99`)
   - Balance fetching works (tested successfully)
   - No 1401 errors

2. **BitMart API Connection:** ✅ Working
   - Balance fetching works

3. **Bot Creation:** ✅ Working
   - Bot created successfully
   - Bot shows as "Running"

---

## 🔍 **Possible Causes**

### **1. Balance Endpoint Not Called**
- Frontend might not be calling `/bots/{bot_id}/balance-and-volume`
- Or endpoint not returning balance data
- Check Network tab in browser DevTools

### **2. Balance Fetching Failing Silently**
- Backend might be failing to fetch balance
- Error might be swallowed/logged but not shown in UI
- Check Hetzner logs: `journalctl -u trading-bridge -f`

### **3. API Credentials Not Loaded**
- Bot might not have exchange credentials
- Or credentials not syncing to exchange_manager
- Check database: `SELECT * FROM exchange_credentials WHERE exchange='coinstore'`

### **4. Frontend Not Parsing Response**
- Balance data might be returned but not displayed
- Check browser console for errors
- Check Network tab for API response

### **5. Bot Not Actually Running**
- Status shows "Running" but bot runner might not be active
- Check Hetzner logs for bot activity
- Check if bot_runner is actually executing trades

---

## 🔧 **What Dev Needs to Check**

### **Step 1: Verify Backend Balance Fetching**

**On Hetzner:**
```bash
# Check if balance endpoint works
curl http://localhost:8080/api/bots/{bot_id}/balance-and-volume

# Check logs for balance fetch attempts
journalctl -u trading-bridge -f | grep -i balance
```

**Expected:** Should return balance data, not zeros

### **Step 2: Check Frontend API Calls**

**In Browser DevTools:**
1. Open Network tab
2. Filter by `/balance` or `/bots`
3. Check if `/bots/{bot_id}/balance-and-volume` is being called
4. Check response - does it have balance data?

### **Step 3: Check Bot Runner**

**On Hetzner:**
```bash
# Check if bot runner is active
journalctl -u trading-bridge -f | grep -i "bot.*running\|volume\|coinstore"
```

**Look for:**
- Bot start messages
- Trade execution logs
- Balance fetch logs

### **Step 4: Verify Exchange Credentials**

**Check Database:**
```sql
SELECT ec.*, cl.account_identifier 
FROM exchange_credentials ec
JOIN clients cl ON cl.id = ec.client_id
JOIN bots b ON b.account = cl.account_identifier
WHERE b.id = '{bot_id}' AND ec.exchange = 'coinstore';
```

**Verify:**
- Credentials exist
- Credentials are decrypted correctly
- Credentials match Coinstore dashboard

---

## 📋 **Quick Diagnostic Commands**

**Test balance endpoint directly:**
```bash
# Replace {bot_id} with actual bot ID
curl http://localhost:8080/api/bots/{bot_id}/balance-and-volume
```

**Check bot status:**
```bash
curl http://localhost:8080/api/bots/{bot_id}
```

**Check exchange connection:**
```bash
curl http://localhost:8080/api/exchange/balance/{account}
```

---

## 🎯 **Most Likely Issue**

**Frontend not calling balance endpoint OR backend not returning balance data.**

**Check:**
1. Browser Network tab - is `/balance-and-volume` endpoint called?
2. Backend logs - any errors when fetching balance?
3. Bot runner - is it actually running and fetching balances?

---

**Dev: Please check these and let me know what you find!**
