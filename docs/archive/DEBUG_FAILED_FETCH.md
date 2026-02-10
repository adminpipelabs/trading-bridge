# Debugging "Failed to Fetch" Error

## 🔍 **What to Check**

### **1. Railway Logs (MOST IMPORTANT)**
```
Railway Dashboard → trading-bridge → Deployments → View Logs
```

Look for:
- Red error lines from the last few minutes
- Stack traces showing where it failed
- Any timeout errors
- Database connection errors

### **2. Check What Part Worked**
Ask the client:
- Did the key get saved? (Check `trading_keys` table)
- Did the bot get created? (Check `bots` table)
- Did anything happen before the error?

### **3. Common Causes**

#### **A. Bot Startup Timeout**
- `bot_runner.start_bot()` might be taking too long
- **Fix:** Already implemented - bot startup failures won't crash the request

#### **B. Database Transaction Issue**
- Multiple `db.commit()` calls might conflict
- **Fix:** Added better transaction handling

#### **C. Missing Dependencies**
- `bot_runner` module might not be available
- **Fix:** Check imports in `main.py`

#### **D. CORS Issue**
- Frontend can't reach backend
- **Fix:** Check CORS settings in `main.py`

### **4. Quick Test**

Test the endpoint directly:
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/clients/{client_id}/setup-bot" \
  -H "Content-Type: application/json" \
  -H "X-Wallet-Address: {wallet_address}" \
  -d '{
    "bot_type": "volume",
    "private_key": "test_key",
    "config": {}
  }'
```

### **5. What the Logs Will Show**

With the new logging, you should see:
```
INFO: Bot record created: {bot_id} for client {client_id}
INFO: Attempting to start bot {bot_id} for client {client_id}
INFO: Bot {bot_id} started successfully for client {client_id}
INFO: Bot setup completed successfully for client {client_id}, bot_id: {bot_id}
```

If any step fails, you'll see:
```
ERROR: Failed to start bot {bot_id}: {error}
ERROR: Unexpected error in setup_bot for client {client_id}: {error}
```

---

## 🎯 **Next Steps**

1. **Check Railway logs** - This will show the exact error
2. **Share the error** - Copy the red error lines from Railway
3. **Check database** - See if bot/key was partially created
4. **Test endpoint** - Use curl to test directly

The code now has comprehensive error handling and logging - the Railway logs will tell us exactly what's failing.
