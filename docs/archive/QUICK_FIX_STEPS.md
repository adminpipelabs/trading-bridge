# Quick Fix - 3 Steps

**Problem:** `HUMMINGBOT_API_URL` is set to `localhost:8000` (wrong)

**Fix:** Set it to the correct Railway service name

---

## 🎯 **Step 1: Find Service Name (30 seconds)**

### **Option A: Railway Dashboard**

1. **Go to Railway Dashboard**
2. **Click your project**
3. **Look at services list** (left sidebar or main view)
4. **Find Hummingbot API service**
5. **Copy the service name** (it's the text/label, not the URL)

**Common names:**
- `hummingbot-api`
- `hummingbot`
- `hummingbot-api-production`
- Or something auto-generated

### **Option B: Check Service Settings**

1. **Click on Hummingbot API service**
2. **Go to "Settings" tab**
3. **Look for "Service Name" or check the URL**
4. **The name is usually in the service URL or settings**

---

## 🔧 **Step 2: Update Trading Bridge Variable (1 minute)**

1. **Go to Trading Bridge service** in Railway
2. **Click "Variables" tab**
3. **Find `HUMMINGBOT_API_URL`**
4. **Click edit/pencil icon**
5. **Change value to:**
   ```
   http://[SERVICE_NAME]:8000
   ```
   **Replace `[SERVICE_NAME]` with the name from Step 1**

   **Example:** If service is `hummingbot-api`, set to:
   ```
   http://hummingbot-api:8000
   ```

6. **Click "Save" or "Update"**

---

## ✅ **Step 3: Wait & Test (2 minutes)**

1. **Wait 1-2 minutes** for Railway to redeploy
2. **Check Trading Bridge logs** - should see:
   ```
   HummingbotClient initialized: http://[SERVICE_NAME]:8000
   ```
   (NOT `localhost:8000`)

3. **Test:**
   ```bash
   curl https://trading-bridge-production.up.railway.app/bots
   ```

---

## 🚀 **If You're Not Sure About Service Name**

**Try these common names:**

1. **Try `hummingbot-api`:**
   - Set `HUMMINGBOT_API_URL=http://hummingbot-api:8000`
   - Wait for redeploy
   - Check logs - if still fails, try next

2. **Try `hummingbot`:**
   - Set `HUMMINGBOT_API_URL=http://hummingbot:8000`
   - Wait for redeploy
   - Check logs

3. **Check Railway logs:**
   - Look for any service discovery or networking logs
   - Might show the actual service name

---

## 📋 **Quick Checklist**

- [ ] Found Hummingbot API service name
- [ ] Updated `HUMMINGBOT_API_URL` in Trading Bridge variables
- [ ] Verified `HUMMINGBOT_API_USERNAME=admin` is set
- [ ] Verified `HUMMINGBOT_API_PASSWORD=admin` is set
- [ ] Waited for redeploy
- [ ] Checked logs show correct URL (not localhost)
- [ ] Tested `/bots` endpoint

---

**That's it! Once you update the variable, Railway will redeploy and it should work.** 🎉
