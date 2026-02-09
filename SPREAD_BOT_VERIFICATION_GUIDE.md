# Spread Bot Verification Guide

**Date:** February 9, 2026  
**Status:** Ready for Testing

---

## 🎯 **Goal**

Verify that the spread bot implementation is working correctly after deployment.

---

## ✅ **Step 1: Verify Deployment**

### **Check Railway Deployment**

1. Go to Railway Dashboard → `trading-bridge` service
2. Check **Deployments** tab
3. Verify latest commit is deployed:
   - Should see commit: `68585ba` - "Implement spread bot with full trading logic"
   - Or commit: `4d2de1c` - "Add implementation summary for dev"

**If not deployed:**
- Wait 2-3 minutes for auto-deploy
- Or manually trigger redeploy

---

## ✅ **Step 2: Check Database - Are Bots Running?**

### **SQL Query:**

```sql
SELECT id, name, status, bot_type, connector, base_asset, quote_asset 
FROM bots 
WHERE status = 'running' 
ORDER BY created_at DESC;
```

**Expected Results:**
- Should see spread bots with `bot_type = 'spread'`
- Should see `status = 'running'`
- Should have `connector` set (e.g., 'bitmart', 'coinstore')
- Should have `base_asset` and `quote_asset` set

**If no spread bots are running:**
- Start a spread bot via UI or API
- Check if bot has API keys configured

---

## ✅ **Step 3: Check Railway Logs - Spread Bot Activity**

### **What to Look For:**

After deployment, watch Railway logs for spread bot activity. You should see:

#### **✅ Good Signs (Bot is Working):**

```
🚀 Spread bot {bot_id} starting for SHARP/USDT
📈 Spread bot {bot_id} - Running cycle
💰 Balance: 10000.0 base, 500.0 quote
📊 Mid price: 0.0001
📖 Orderbook: bid=0.00009, ask=0.00011, mid=0.0001
📍 Target prices - Bid: 0.000099, Ask: 0.000101
📝 Placing buy order: 1000.0 @ 0.000099
✅ Order placed: order-12345
📝 Placing sell order: 1000.0 @ 0.000101
✅ Order placed: order-12346
✅ Cycle complete. Active orders: 2
```

#### **❌ Bad Signs (Bot Has Issues):**

```
❌ Spread bot {bot_id} cycle error: ...
❌ Balance fetch error: ...
❌ Orderbook fetch error: ...
❌ Order placement error: ...
```

#### **⚠️ Still Placeholder (Code Not Deployed):**

```
📈 Spread bot {bot_id} - Refreshing orders...
⚠️  Spread bot logic not yet implemented
```

**If you see the placeholder message:** Code hasn't deployed yet, wait for deployment.

---

## ✅ **Step 4: Check Exchange - Are Orders Being Placed?**

### **For BitMart:**
1. Log into BitMart dashboard
2. Go to **Spot Trading** → **Open Orders**
3. Look for orders placed by the bot
4. Should see bid (buy) and ask (sell) orders around mid price

### **For Coinstore:**
1. Log into Coinstore dashboard
2. Go to **Spot Trading** → **Orders**
3. Look for open orders
4. Should see bid/ask orders

**Expected:**
- Bid order at `mid - (spread/2)`
- Ask order at `mid + (spread/2)`
- Orders refresh every 30 seconds

---

## ✅ **Step 5: Test Balance Fetch**

### **Via API:**

```bash
# Replace {bot_id} with actual bot ID
curl "https://trading-bridge-production.up.railway.app/api/bots/{bot_id}/stats" | jq
```

**Expected Response:**
```json
{
  "available": {
    "SHARP": 10000.0,
    "USDT": 500.0
  },
  "locked": {
    "SHARP": 0,
    "USDT": 0
  },
  "volume_24h": 0,
  "trades_24h": {
    "buys": 0,
    "sells": 0
  }
}
```

**If still shows 0:**
- Check Railway logs for error messages
- See `BALANCE_TRADING_ISSUES_SUMMARY_FOR_DEV.md` for investigation steps

---

## ✅ **Step 6: Check Bot Runner Status**

### **Look for Bot Runner Logs:**

```
STARTING BOT RUNNER SERVICE
Found X bot(s) with status='running'
✅ Bot {bot_id} started successfully
```

**If bot runner isn't starting:**
- Check if `CEXBotRunner` is initialized in `main.py`
- Check Railway logs for startup errors

---

## 📋 **Verification Checklist**

- [ ] Railway deployment shows latest commit
- [ ] Database shows spread bots with `status = 'running'`
- [ ] Railway logs show spread bot activity (not placeholder)
- [ ] Logs show orderbook fetching
- [ ] Logs show order placement
- [ ] Exchange dashboard shows open orders
- [ ] Balance fetch returns non-zero values (or shows clear error)
- [ ] Bot runner is running and picking up bots

---

## 🚨 **Common Issues**

### **Issue 1: Still Seeing Placeholder Message**

**Symptom:** Logs show "Spread bot logic not yet implemented"

**Fix:** 
- Wait for Railway to deploy
- Check deployment status in Railway dashboard
- Manually trigger redeploy if needed

---

### **Issue 2: Bot Not Starting**

**Symptom:** Bot status is "running" but no logs appear

**Check:**
- Is bot runner service running?
- Does bot have API keys configured?
- Check Railway logs for startup errors

---

### **Issue 3: Balance Fetch Errors**

**Symptom:** Balance shows 0, logs show errors

**Check:**
- Are API keys valid? (test with curl)
- Is IP whitelisted? (Railway IP: `54.205.35.75`)
- Check `BALANCE_TRADING_ISSUES_SUMMARY_FOR_DEV.md` for detailed steps

---

### **Issue 4: Orders Not Placing**

**Symptom:** Bot runs but no orders appear on exchange

**Check:**
- Does bot have sufficient balance?
- Are order sizes too small?
- Check logs for order placement errors
- Verify exchange API permissions (spot trading enabled?)

---

## 📝 **Log Collection**

**For CTO/Dev Review:**

Collect these logs:

1. **Last 100 lines of Railway logs** after a spread bot cycle runs
2. **Bot runner startup logs** (first 50 lines)
3. **Any error messages** (search for "❌" or "ERROR")
4. **Balance fetch response** (from API test)

**Command to get logs:**
```bash
# Via Railway CLI or dashboard
railway logs --tail 100
```

---

## 🎯 **Success Criteria**

**Spread Bot is Working If:**
- ✅ Logs show orderbook fetching
- ✅ Logs show order placement
- ✅ Exchange shows open orders
- ✅ Orders refresh every 30 seconds
- ✅ No errors in logs

**If all criteria met:** ✅ Spread bot implementation is successful!

**If not:** Check logs for specific errors and see troubleshooting section above.

---

## 📞 **Next Steps After Verification**

1. **If working:** Document success, move on to fixing balance/trading issues
2. **If not working:** Collect logs and errors, investigate root cause
3. **If partial:** Identify what's working vs what's broken

---

**Document prepared for:** CTO / Development Team  
**Ready for:** Testing and verification
