# Fix Connection Issue

**Problem Found:** ✅

**Error:**
```
Connection failed to http://localhost:8000/bot-orchestration/status
```

**Meaning:** `HUMMINGBOT_API_URL` is not set correctly, defaulting to `localhost:8000`

---

## 🔧 **Fix Steps**

### **Step 1: Find Hummingbot API Service Name**

1. **Railway Dashboard** → Your Project
2. **Look at services list**
3. **What is Hummingbot API service called?**
   - Common names: `hummingbot-api`, `hummingbot`, or auto-generated name

### **Step 2: Set Correct URL in Trading Bridge**

1. **Go to Trading Bridge service**
2. **Click "Variables" tab**
3. **Find `HUMMINGBOT_API_URL`**
4. **Change it to:**
   ```
   http://[SERVICE_NAME]:8000
   ```
   
   **Replace `[SERVICE_NAME]` with actual service name**
   
   **Examples:**
   - If service is `hummingbot-api`: `http://hummingbot-api:8000`
   - If service is `hummingbot`: `http://hummingbot:8000`

### **Step 3: Verify All Variables**

**Make sure these are set:**
- ✅ `HUMMINGBOT_API_URL=http://[SERVICE_NAME]:8000`
- ✅ `HUMMINGBOT_API_USERNAME=admin`
- ✅ `HUMMINGBOT_API_PASSWORD=admin`

### **Step 4: Wait for Redeploy**

Railway will auto-redeploy when you change variables.

### **Step 5: Test**

After redeploy, test again:
```bash
curl https://trading-bridge-production.up.railway.app/bots
```

---

## 🎯 **What Service Name to Use?**

**Check Railway project overview:**
- Look at list of services
- Find the Hummingbot API service
- Use that exact name

**If unsure, try:**
- `http://hummingbot-api:8000`
- `http://hummingbot:8000`

---

## ✅ **After Fix**

**Check Trading Bridge logs:**
- Should see: `HummingbotClient initialized: http://[SERVICE_NAME]:8000`
- Should NOT see: `localhost:8000`

**Then test bot creation again!**
