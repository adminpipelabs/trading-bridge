# Phase 3: Configure Trading Bridge - Step by Step

**Goal:** Connect Trading Bridge to Hummingbot API  
**Status:** ✅ Hummingbot API deployed, ✅ Postgres running

---

## ✅ **STEP 3.1: Get Hummingbot Service URL**

### **Action:**

1. **Go to Railway Dashboard**
   - Select your project
   - Click on **Hummingbot API** service

2. **Get Internal Service Name:**
   - Go to **Settings** → **Networking**
   - Look for **Service Name** or **Internal URL**
   - OR check **Variables** tab for `RAILWAY_SERVICE_NAME`

**Common formats:**
- Service name: `hummingbot-api` (if you named it that)
- Internal URL: `http://hummingbot-api:8000`
- OR: `http://<service-name>:8000`

**✅ Verify:** Have service name/URL

**Status:** [ ] Complete - Service URL obtained

---

## ✅ **STEP 3.2: Set Trading Bridge Environment Variables**

### **Action:**

1. **Go to Trading Bridge Service**
   - Railway Dashboard → Your Project → **Trading Bridge** service

2. **Open Variables Tab**
   - Click **Variables** tab

3. **Add These Variables:**

```bash
HUMMINGBOT_API_URL=http://hummingbot-api:8000
HUMMINGBOT_API_USERNAME=admin
HUMMINGBOT_API_PASSWORD=admin
```

**Important:**
- Replace `hummingbot-api` with your actual service name if different
- Use internal URL format: `http://<service-name>:8000`
- No `https://` - use `http://` for internal communication

**✅ Verify:** All three variables added

**Status:** [ ] Complete - Variables set

---

## ✅ **STEP 3.3: Redeploy Trading Bridge**

### **Action:**

1. **Railway will auto-redeploy** when you add variables

2. **Monitor Deployment:**
   - Go to **Deployments** tab
   - Watch for "Deployment successful"
   - Check **Logs** tab

**Look for in logs:**
- "HummingbotClient initialized: http://hummingbot-api:8000"
- "Application startup complete"
- Any connection errors

**✅ Verify:** Deployment successful, no errors

**Status:** [ ] Complete - Trading Bridge redeployed

---

## ✅ **STEP 3.4: Test Connection**

### **Action:**

**Test 1: Trading Bridge Root**
```bash
curl https://trading-bridge-production.up.railway.app/
```

**Expected:**
```json
{"service":"Trading Bridge","version":"1.0.0","status":"online"}
```

**Test 2: Get Bots (from Hummingbot)**
```bash
curl https://trading-bridge-production.up.railway.app/bots
```

**Expected:**
```json
{
  "bots": [
    // List of bots from Hummingbot, or empty array []
  ]
}
```

**If empty array:** That's OK - means connection works, just no bots yet!

**Test 3: Create Bot**
```bash
curl -X POST "https://trading-bridge-production.up.railway.app/bots/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_bot_production",
    "account": "client_sharp",
    "connector": "bitmart",
    "pair": "SHARP/USDT",
    "strategy": "spread",
    "config": {
      "bid_spread": 0.001,
      "ask_spread": 0.001,
      "order_amount": 100
    }
  }'
```

**Expected:**
```json
{
  "id": "test_bot_production",
  "name": "test_bot_production",
  "status": "running",
  "strategy": "spread",
  "connector": "bitmart",
  "pair": "SHARP/USDT",
  ...
}
```

**✅ Verify:** All tests pass

**Status:** [ ] Complete - Connection tested

---

## 📋 **Phase 3 Checklist**

- [ ] Step 3.1: Got Hummingbot service URL
- [ ] Step 3.2: Set Trading Bridge variables
- [ ] Step 3.3: Trading Bridge redeployed
- [ ] Step 3.4: Tested connection
- [ ] Step 3.5: Tested bot creation

---

## 🚨 **Troubleshooting**

### **Issue: Can't find service name**

**Check:**
- Railway → Hummingbot API → Settings → Networking
- Look for "Service Name" or internal DNS name
- Common names: `hummingbot-api`, `hummingbot`, or auto-generated name

**Solution:** Use whatever name Railway shows, format: `http://<name>:8000`

---

### **Issue: Connection refused**

**Check:**
- Hummingbot API service name correct?
- Port 8000 configured?
- Both services in same Railway project?

**Solution:** Verify service name, check Hummingbot API logs

---

### **Issue: Not authenticated**

**Check:**
- `HUMMINGBOT_API_USERNAME=admin` set?
- `HUMMINGBOT_API_PASSWORD=admin` set?

**Solution:** Verify credentials match Hummingbot API

---

## 🎯 **Quick Steps**

1. **Get Hummingbot service name** (from Settings → Networking)
2. **Go to Trading Bridge** → Variables
3. **Add:**
   ```
   HUMMINGBOT_API_URL=http://<service-name>:8000
   HUMMINGBOT_API_USERNAME=admin
   HUMMINGBOT_API_PASSWORD=admin
   ```
4. **Wait for redeploy**
5. **Test:** `curl https://trading-bridge-production.up.railway.app/bots`

---

**Ready to start Step 3.1?** 🚀
