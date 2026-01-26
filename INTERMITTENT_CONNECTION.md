# Intermittent Connection Issue

**Status:** ⚠️ `/bots` endpoint works, but bot creation fails

---

## 🔍 **Current Situation**

### **What Works:**
- ✅ `GET /bots` - Returns `{"bots":[]}` successfully
- ✅ Environment variables configured correctly
- ✅ Bot manager initializes

### **What Fails:**
- ❌ `POST /bots/create` - Connection fails when calling Hummingbot API
- ❌ Error: `[Errno -2] Name or service not known`
- ❌ Fails when calling `/bot-orchestration/deploy-v2-script`

---

## 🤔 **Analysis**

**Why `/bots` works but creation fails:**

1. **`/bots` endpoint** calls `get_status()` which might:
   - Use cached connection
   - Have different timeout
   - Work with initial connection

2. **Bot creation** calls `deploy_script()` which:
   - Makes new connection
   - Different endpoint
   - Might hit DNS resolution issue

---

## 🔧 **Possible Causes**

### **1. Hummingbot API Not Running**
- Service might have stopped
- Check Hummingbot API logs
- Verify it's actually running

### **2. Intermittent DNS**
- Railway DNS might be flaky
- Service name resolves sometimes, not always
- Network timing issue

### **3. Service Name Still Wrong**
- Might work for some endpoints, not others
- Need to verify actual service name

---

## 🔍 **What to Check**

### **Step 1: Verify Hummingbot API is Running**

**Go to Hummingbot API service:**
1. **Logs tab**
2. **Should see:** `INFO: Uvicorn running on http://0.0.0.0:8000`
3. **Check for errors** or stopped status

### **Step 2: Test Hummingbot API Directly**

**If you have access, test:**
```bash
# From Railway or local machine
curl http://hummingbot-api:8000/bot-orchestration/status
```

**Or if public URL available:**
```bash
curl https://hummingbot-api-production.up.railway.app/bot-orchestration/status
```

### **Step 3: Check Service Name**

**Verify in Railway:**
- What is Hummingbot API service actually called?
- Is it `hummingbot-api` or something else?

---

## 🔧 **Potential Fixes**

### **Fix 1: Use Public URL**

**If internal DNS is unreliable:**

1. **Get Hummingbot API public domain**
2. **Update Trading Bridge variable:**
   ```
   HUMMINGBOT_API_URL=https://hummingbot-api-production.up.railway.app
   ```
3. **Enable public access** on Hummingbot API

### **Fix 2: Add Retry Logic**

**Add retry mechanism for connection failures:**
- Retry DNS resolution
- Exponential backoff
- Better error handling

### **Fix 3: Verify Service Name**

**Double-check actual service name:**
- Try different variations
- Check Railway service settings
- Use exact name from Railway

---

## 📋 **Next Steps**

1. **Check Hummingbot API logs** - Is it running?
2. **Verify service name** - What is it actually called?
3. **Test direct connection** - Can we reach Hummingbot API?
4. **Consider public URL** - If internal DNS unreliable

---

**Please check Hummingbot API logs and service name!** 🔍
