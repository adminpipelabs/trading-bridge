# Find Hummingbot API Service

**Issue:** Can't resolve `hummingbot-api` - service name not found

---

## 🔍 **What We Know**

### **Trading Bridge Logs Show:**
- ✅ Trading Bridge running successfully
- ✅ `/bots` endpoint returns 200 OK
- ❌ Connection fails: `[Errno -2] Name or service not known`
- ❌ Can't reach `http://hummingbot-api:8000`

### **Hummingbot Logs Show:**
- ✅ PostgreSQL database running
- ❌ **No Hummingbot API logs** (no "Uvicorn running" message)

---

## 🎯 **The Problem**

**We only see PostgreSQL logs, not Hummingbot API logs.**

This suggests:
1. **Hummingbot API service might not be running**
2. **Or it's a different service/deployment**
3. **Or the service name is different**

---

## 🔧 **What to Check**

### **Step 1: Find Hummingbot API Service**

**In Railway Dashboard:**

1. **Go to your Railway project**
2. **Look at services list**
3. **How many services do you see?**
   - Trading Bridge ✅
   - PostgreSQL ✅ (for Hummingbot)
   - **Hummingbot API?** ❓

**Questions:**
- Is there a separate "Hummingbot API" service?
- Or is Hummingbot API part of another service?
- What is it actually called?

### **Step 2: Check Hummingbot API Logs**

**If there's a Hummingbot API service:**

1. **Click on it**
2. **Go to "Logs" tab**
3. **Look for:**
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   INFO:     Application startup complete
   ```

**If you don't see these logs:**
- Service might not be running
- Or it's not deployed yet
- Or it's called something else

### **Step 3: Verify Service Name**

**If Hummingbot API service exists:**

1. **Check service name/label**
2. **What is it actually called?**
   - `hummingbot-api`?
   - `hummingbot`?
   - Something else?

3. **Update Trading Bridge variable:**
   ```
   HUMMINGBOT_API_URL=http://[ACTUAL_SERVICE_NAME]:8000
   ```

---

## 📋 **Possible Scenarios**

### **Scenario 1: Service Not Deployed**
- Hummingbot API hasn't been deployed to Railway yet
- Need to deploy it first

### **Scenario 2: Wrong Service Name**
- Service exists but called something else
- Need to find correct name

### **Scenario 3: Different Project**
- Services in different Railway projects
- Need to move to same project or use public URL

### **Scenario 4: Service Not Running**
- Service exists but failed to start
- Check deployment errors

---

## ✅ **What We Need**

**Please check and share:**

1. **How many services in your Railway project?**
   - List all service names

2. **Is there a Hummingbot API service?**
   - What is it called?
   - Is it running?

3. **Hummingbot API logs:**
   - Do you see "Uvicorn running"?
   - Any errors?

---

## 🚀 **Next Steps**

**Once we know:**
1. **If service exists:** Update service name in Trading Bridge
2. **If not deployed:** Deploy Hummingbot API to Railway
3. **If different project:** Move to same project or use public URL

---

**Please check Railway services list and share what you find!** 🔍
