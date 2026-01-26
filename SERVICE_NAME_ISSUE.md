# Service Name Resolution Issue

**Status:** ✅ Environment variables working  
**New Issue:** Service name `hummingbot-api` not resolving

---

## ✅ **What's Working**

- ✅ Environment variables are being read correctly
- ✅ `HUMMINGBOT_API_URL=http://hummingbot-api:8000` is set
- ✅ Application starts successfully
- ✅ Bot manager initializes

---

## ❌ **Current Issue**

**Error:**
```
Connection failed to http://hummingbot-api:8000/bot-orchestration/status: 
[Errno -2] Name or service not known
```

**Meaning:** Railway can't resolve the service name `hummingbot-api`

---

## 🔍 **Possible Causes**

### **1. Wrong Service Name**
- Service might be called something else (not `hummingbot-api`)
- Check actual service name in Railway

### **2. Services in Different Projects**
- Both services must be in **same Railway project**
- Internal DNS only works within same project

### **3. Hummingbot API Not Running**
- Service might be stopped or failed to start
- Check Hummingbot API logs

### **4. Railway Internal DNS Issue**
- Sometimes Railway's internal DNS takes time
- Or service discovery isn't working

---

## 🔧 **How to Fix**

### **Step 1: Find Actual Service Name**

**In Railway Dashboard:**
1. Go to your project
2. Look at services list
3. **What is Hummingbot API service actually called?**
   - Common names: `hummingbot-api`, `hummingbot`, `service-xxxxx`
   - Check service settings/overview

### **Step 2: Verify Same Project**

**Check:**
- Are Trading Bridge and Hummingbot API in the **same Railway project**?
- If different projects, internal DNS won't work

### **Step 3: Check Hummingbot API Status**

**Go to Hummingbot API service:**
1. Click on service
2. Check **Logs** tab
3. Should see: `INFO: Uvicorn running on http://0.0.0.0:8000`
4. If not running, check deployment errors

### **Step 4: Update Service Name**

**If service name is different:**
1. Trading Bridge → Variables
2. Update `HUMMINGBOT_API_URL` to correct service name
3. Example: `http://hummingbot:8000` (if that's the actual name)
4. Wait for redeploy

---

## 🎯 **What We Need**

**Please check and share:**

1. **What is the Hummingbot API service actually called?**
   - Check Railway project → services list
   - Or service settings/overview

2. **Are both services in the same Railway project?**
   - Trading Bridge and Hummingbot API should be in same project

3. **Is Hummingbot API running?**
   - Check logs for "Uvicorn running"
   - Check deployment status

---

## 📋 **Alternative: Use Public URL**

**If internal DNS doesn't work, try public URL:**

1. **Get Hummingbot API public URL:**
   - Railway Dashboard → Hummingbot API service
   - Settings → Generate Domain (or check existing domain)
   - Should be something like: `hummingbot-api-production.up.railway.app`

2. **Update Trading Bridge variable:**
   ```
   HUMMINGBOT_API_URL=https://hummingbot-api-production.up.railway.app
   ```
   (Use HTTPS and public domain)

3. **Note:** This requires Hummingbot API to be publicly accessible

---

## ✅ **Quick Test**

**After finding correct service name:**

1. Update `HUMMINGBOT_API_URL` in Trading Bridge
2. Wait for redeploy
3. Check logs - should see successful connection
4. Test: `curl https://trading-bridge-production.up.railway.app/bots`

---

**Please share the actual Hummingbot API service name!** 🔍
